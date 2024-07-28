import librosa
import numpy as np
from pydub import AudioSegment
import io
import os
import random
import speech_recognition as sr
from difflib import Differ
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense, Lambda, Dropout, BatchNormalization
import tensorflow.keras.backend as K
from sklearn.preprocessing import StandardScaler
import tensorflow as tf

# 明確指定ffmpeg和ffprobe的路徑
AudioSegment.converter = "C:/ffmpeg/bin/ffmpeg.exe"
AudioSegment.ffprobe = "C:/ffmpeg/bin/ffprobe.exe"

# 預處理語音數據
def preprocess_audio(file_path):
    print(f"正在預處理音頻: {file_path}")
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
    return y, sr

# 特徵提取（使用MFCC）
def extract_features(audio, sr):
    print("正在提取特徵")
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    return np.mean(mfccs.T, axis=0)

# 数据增强
def augment_audio(audio, sr):
    print("正在進行數據增強")
    # 添加噪音
    noise = np.random.randn(len(audio))
    audio_noise = audio + 0.005 * noise
    # 改变音调
    audio_shift = librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=4)
    # 改变速度
    audio_stretch = librosa.effects.time_stretch(y=audio, rate=0.8)
    return [audio, audio_noise, audio_shift, audio_stretch]

# 創建數據集
def create_dataset(data_directory, num_samples=10):  # 減少樣本數量以加快測試
    # 打印數據目錄路徑
    print(f"數據目錄: {data_directory}")
    
    # 獲取所有音頻文件
    audio_files = [os.path.join(data_directory, f) for f in os.listdir(data_directory) if f.endswith('.mp3')]
    
    # 打印找到的音頻文件數量
    print(f"找到 {len(audio_files)} 個音頻文件")
    
    same_audio_pairs = []
    diff_audio_pairs = []
    
    # 如果沒有音頻文件，拋出錯誤
    if len(audio_files) == 0:
        raise ValueError("未找到任何音頻文件，請確認數據目錄是否正確並包含音頻文件")
    
    # 創建相似對（正例）
    print("創建相似對（正例）")
    for _ in range(num_samples):
        file1 = random.choice(audio_files)
        file2 = random.choice(audio_files)
        while file2 == file1:
            file2 = random.choice(audio_files)
        same_audio_pairs.append((file1, file2))
    
    # 創建不相似對（反例）
    print("創建不相似對（反例）")
    for _ in range(num_samples):
        file1 = random.choice(audio_files)
        file2 = random.choice(audio_files)
        while file2 == file1:
            file2 = random.choice(audio_files)
        diff_audio_pairs.append((file1, file2))
    
    return same_audio_pairs, diff_audio_pairs

# 定義Siamese Network結構
def build_base_network(input_shape):
    input = Input(input_shape)
    x = Dense(128, activation='relu')(input)
    x = Dropout(0.2)(x)
    x = BatchNormalization()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.2)(x)
    x = BatchNormalization()(x)
    x = Dense(128, activation='relu')(x)
    return Model(input, x)

# 自定義歐幾里得距離函數
def euclidean_distance(vectors):
    x, y = vectors
    return K.sqrt(K.sum(K.square(x - y), axis=1, keepdims=True))

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
    
    distance = Lambda(euclidean_distance, output_shape=(1,))([left_output, right_output])
    
    model = Model([left_input, right_input], distance)
    model.compile(loss=contrastive_loss, optimizer='adam')
    return model

# 將音頻轉換為WAV格式
def convert_to_wav(file_path):
    if file_path.endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
        wav_path = file_path.replace('.mp3', '.wav')
        audio.export(wav_path, format='wav')
        return wav_path
    return file_path

# 語音轉文字
def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    audio_path = convert_to_wav(audio_path)
    audio_file = sr.AudioFile(audio_path)
    with audio_file as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = ""
    return text

# 比較兩段文字並顯示不同之處
def compare_texts(text1, text2):
    d = Differ()
    diff = list(d.compare(text1.split(), text2.split()))
    print("不同之處:")
    for line in diff:
        if line.startswith('+ ') or line.startswith('- '):
            print(line)

# 主程序
if __name__ == "__main__":
    # 設置數據目錄
    data_directory = os.path.join(os.getcwd(), "data")
    
    # 創建數據集
    same_audio_files, diff_audio_files = create_dataset(data_directory, num_samples=5)  # 減少樣本數量以加快測試

    num_pairs = len(same_audio_files) + len(diff_audio_files)
    X_left = []
    X_right = []
    y = []

    # 構建語音對和標籤
    print("構建語音對和標籤")
    for i, (file1, file2) in enumerate(same_audio_files):
        audio_1, sr_1 = preprocess_audio(file1)
        audio_2, sr_2 = preprocess_audio(file2)
        for aug_audio_1 in augment_audio(audio_1, sr_1):
            for aug_audio_2 in augment_audio(audio_2, sr_2):
                X_left.append(extract_features(aug_audio_1, sr_1))
                X_right.append(extract_features(aug_audio_2, sr_2))
                y.append(1)  # 標註為正例

    for i, (file1, file2) in enumerate(diff_audio_files, start=len(same_audio_files)):
        audio_1, sr_1 = preprocess_audio(file1)
        audio_2, sr_2 = preprocess_audio(file2)
        for aug_audio_1 in augment_audio(audio_1, sr_1):
            for aug_audio_2 in augment_audio(audio_2, sr_2):
                X_left.append(extract_features(aug_audio_1, sr_1))
                X_right.append(extract_features(aug_audio_2, sr_2))
                y.append(0)  # 標註為反例

    X_left = np.array(X_left)
    X_right = np.array(X_right)
    y = np.array(y)

    # 標準化特徵
    print("標準化特徵")
    scaler = StandardScaler()
    X_left = scaler.fit_transform(X_left)
    X_right = scaler.transform(X_right)

    # 訓練模型
    print("訓練模型")
    input_shape = (13,)
    model = create_siamese_network(input_shape)
    model.fit([X_left, X_right], y, batch_size=2, epochs=10, validation_split=0.2)  # 減少批次大小和訓練輪數以加快測試

    # 保存模型
    model.save('siamese_network_model.h5')

    # 加載模型並進行測試
    print("加載模型並進行測試")
    model = load_model('siamese_network_model.h5', custom_objects={'contrastive_loss': contrastive_loss, 'euclidean_distance': euclidean_distance})

    test_pairs = [
        (os.path.join(data_directory, 'common_voice_en_1105.mp3'), os.path.join(data_directory, 'common_voice_en_1106.mp3')),
        (os.path.join(data_directory, 'common_voice_en_1107.mp3'), os.path.join(data_directory, 'common_voice_en_1108.mp3')),
    ]
    test_labels = [1, 0]  # 正確的標籤，假設第一對是一致的，第二對是不一致的

    correct_predictions = 0

    for i, (file1, file2) in enumerate(test_pairs):
        audio_1, sr_1 = preprocess_audio(file1)
        audio_2, sr_2 = preprocess_audio(file2)

        new_features_1 = extract_features(audio_1, sr_1)
        new_features_2 = extract_features(audio_2, sr_2)

        # 標準化測試特徵
        new_features_1 = scaler.transform(new_features_1.reshape(1, -1))
        new_features_2 = scaler.transform(new_features_2.reshape(1, -1))

        distance = model.predict([new_features_1, new_features_2])[0][0]
        threshold = 0.5  # 閾值
        print(f"測試對 {i+1} 距離值: {distance}")

        if (distance < threshold and test_labels[i] == 1) or (distance >= threshold and test_labels[i] == 0):
            print(f"測試對 {i+1} 判斷正確")
            correct_predictions += 1
        else:
            print(f"測試對 {i+1} 判斷錯誤")

    overall_accuracy = correct_predictions / len(test_pairs) * 100
    print(f"模型整體正確率: {overall_accuracy:.2f}%")

    # 進行語音轉文字比較
    for i, (file1, file2) in enumerate(test_pairs):
        text1 = speech_to_text(file1)
        text2 = speech_to_text(file2)

        print(f"語音對 {i+1} 的文字轉換結果:")
        print(f"語音1: {text1}")
        print(f"語音2: {text2}")

        compare_texts(text1, text2)
