import librosa
import numpy as np
from pydub import AudioSegment
import io
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Lambda
import tensorflow.keras.backend as K
from tensorflow.keras.models import load_model
import os

# 預處理語音數據
def preprocess_audio(file_path):
    # 使用pydub將MP3轉換為WAV
    if file_path.endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
        file_handle = io.BytesIO()
        audio.export(file_handle, format='wav')
        file_handle.seek(0)
        y, sr = librosa.load(file_handle, sr=16000)
    else:
        y, sr = librosa.load(file_path, sr=16000)
    
    y = librosa.effects.trim(y)[0]  # 去掉靜音部分
    y = librosa.util.fix_length(y, size=16000)  # 調整長度到1秒（假設語音長度為1秒）
    return y

# 特徵提取（使用MFCC）
def extract_features(audio):
    mfccs = librosa.feature.mfcc(y=audio, sr=16000, n_mfcc=13)
    return np.mean(mfccs.T, axis=0)

# 定義Siamese Network結構
def build_base_network(input_shape):
    input = Input(input_shape)
    x = Dense(128, activation='relu')(input)
    x = Dense(128, activation='relu')(x)
    x = Dense(128, activation='relu')(x)
    return Model(input, x)

# 定義對比損失函數
def contrastive_loss(y_true, y_pred):
    margin = 1
    return K.mean(y_true * K.square(y_pred) + (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))

# 構建Siamese Network
def create_siamese_network(input_shape):
    left_input = Input(input_shape)
    right_input = Input(input_shape)
    
    base_network = build_base_network(input_shape)
    
    left_output = base_network(left_input)
    right_output = base_network(right_input)
    
    def euclidean_distance(vectors):
        x, y = vectors
        return K.sqrt(K.sum(K.square(x - y), axis=1, keepdims=True))
    
    distance = Lambda(euclidean_distance, output_shape=(1,))([left_output, right_output])
    
    model = Model([left_input, right_input], distance)
    model.compile(loss=contrastive_loss, optimizer='adam')
    return model

# 主程序
if __name__ == "__main__":
    # 設置語音文件路徑
    same_audio_files = [('audio_file_1.mp3', 'audio_file_2.mp3')] * 500
    diff_audio_files = [('audio_file_3.mp3', 'audio_file_4.mp3')] * 500

    num_pairs = len(same_audio_files) + len(diff_audio_files)
    X_left = np.zeros((num_pairs, 13))
    X_right = np.zeros((num_pairs, 13))
    y = np.zeros((num_pairs,))

    # 構建語音對和標籤
    for i, (file1, file2) in enumerate(same_audio_files):
        audio_1 = preprocess_audio(file1)
        audio_2 = preprocess_audio(file2)
        X_left[i] = extract_features(audio_1)
        X_right[i] = extract_features(audio_2)
        y[i] = 1  # 標註為正例

    for i, (file1, file2) in enumerate(diff_audio_files, start=len(same_audio_files)):
        audio_1 = preprocess_audio(file1)
        audio_2 = preprocess_audio(file2)
        X_left[i] = extract_features(audio_1)
        X_right[i] = extract_features(audio_2)
        y[i] = 0  # 標註為反例

    # 訓練模型
    input_shape = (13,)
    model = create_siamese_network(input_shape)
    model.fit([X_left, X_right], y, batch_size=32, epochs=10, validation_split=0.2)

    # 保存模型
    model.save('siamese_network_model.h5')

    # 加載模型並進行測試
    model = load_model('siamese_network_model.h5', custom_objects={'contrastive_loss': contrastive_loss})

    # 測試新的語音對
    new_audio_1 = preprocess_audio('new_audio_file_1.mp3')
    new_audio_2 = preprocess_audio('new_audio_file_2.mp3')

    new_features_1 = extract_features(new_audio_1)
    new_features_2 = extract_features(new_audio_2)

    distance = model.predict([new_features_1.reshape(1, -1), new_features_2.reshape(1, -1)])
    threshold = 0.5  # 閾值
    if distance < threshold:
        print("內容一致")
    else:
        print("內容不一致")
