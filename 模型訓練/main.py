import librosa
import numpy as np
from pydub import AudioSegment
import io
import os
import joblib
from tensorflow.keras.models import load_model
import tensorflow.keras.backend as K
from sklearn.preprocessing import StandardScaler

# 自定义欧几里得距离函数
def euclidean_distance(vectors):
    x, y = vectors
    return K.sqrt(K.sum(K.square(x - y), axis=1, keepdims=True))

# 定义对比损失函数
def contrastive_loss(y_true, y_pred):
    margin = 1
    return K.mean(y_true * K.square(y_pred) + (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))

# 预处理语音数据
def preprocess_audio(file_path, target_length=16000):
    if file_path.endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
        file_handle = io.BytesIO()
        audio.export(file_handle, format='wav')
        file_handle.seek(0)
        y, sr = librosa.load(file_handle, sr=16000)
    else:
        y, sr = librosa.load(file_path, sr=16000)
    
    y = librosa.effects.trim(y)[0]
    y = librosa.util.fix_length(y, size=target_length)
    return y, sr

# 提取特征
def extract_features(audio, sr):
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
    chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
    mel = librosa.feature.melspectrogram(y=audio, sr=sr)
    contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
    tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(audio), sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y=audio)
    spec_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
    spec_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
    
    features = np.concatenate((
        np.mean(mfccs.T, axis=0), 
        np.mean(chroma.T, axis=0), 
        np.mean(mel.T, axis=0), 
        np.mean(contrast.T, axis=0), 
        np.mean(tonnetz.T, axis=0),
        np.mean(zcr.T, axis=0),
        np.mean(spec_rolloff.T, axis=0),
        np.mean(spec_centroid.T, axis=0)
    ))
    return features

# 将音频转换为WAV格式
def convert_to_wav(file_path):
    if file_path.endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
        wav_path = file_path.replace('.mp3', '.wav')
        audio.export(wav_path, format='wav')
        return wav_path
    return file_path

# 加载模型和标量
model = load_model('siamese_network_model.h5', custom_objects={'contrastive_loss': contrastive_loss, 'euclidean_distance': euclidean_distance})
scaler = joblib.load('scaler.pkl')

# 定义要比较的音频对
data_directory = os.path.join(os.getcwd(), "data")
test_pairs = [
    (os.path.join(data_directory, 'common_voice_en_11029.wav'), os.path.join(data_directory, 'parler_tts_out_11028.wav')),
    (os.path.join(data_directory, 'common_voice_en_11029.wav'), os.path.join(data_directory, 'parler_tts_out_11029.wav')),
]

# 测试模型
for i, (file1, file2) in enumerate(test_pairs):
    audio_1, sr_1 = preprocess_audio(file1)
    audio_2, sr_2 = preprocess_audio(file2)

    new_features_1 = extract_features(audio_1, sr_1)
    new_features_2 = extract_features(audio_2, sr_2)

    # 使用加载的标准化器进行标准化
    new_features_1 = scaler.transform(new_features_1.reshape(1, -1))
    new_features_2 = scaler.transform(new_features_2.reshape(1, -1))

    distance = model.predict([new_features_1, new_features_2])[0][0]
    print(f"測試對 {i+1} 距離值: {distance}")

    threshold = 0.5  # 可以根据实际情况调整阈值
    if distance < threshold:
        print(f"測試對 {i+1} 被判斷為相似")
    else:
        print(f"測試對 {i+1} 被判斷為不相似")
