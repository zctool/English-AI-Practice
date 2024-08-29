import speech_recognition as sr
from pyannote.audio import Model, Inference
from scipy.spatial.distance import cosine
from difflib import SequenceMatcher

def recognize_speech(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return ""

def extract_audio_embedding(file_path):
    model = Model.from_pretrained("pyannote/embedding", use_auth_token="HUGGINGFACE_ACCESS_TOKEN_GOES_HERE")
    inference = Inference(model, window="whole")
    embedding = inference(file_path)
    return embedding

def compare_audio_embeddings(embedding1, embedding2):
    similarity = 1 - cosine(embedding1, embedding2)
    return similarity

def compare_text(text1, text2):
    words1 = text1.split()
    words2 = text2.split()
    return SequenceMatcher(None, words1, words2).ratio(), SequenceMatcher(None, words1, words2).get_opcodes()

embedding1 = extract_audio_embedding("data/common_voice_en_11425.wav")
embedding2 = extract_audio_embedding("data/parler_tts_out_11425.wav")

similarity_score = compare_audio_embeddings(embedding1, embedding2)

text1 = recognize_speech("data/common_voice_en_11425.wav")
text2 = recognize_speech("data/parler_tts_out_11425.wav")

text_similarity, diff_ops = compare_text(text1, text2)

audio_threshold = 0.1
text_threshold = 0.99

if similarity_score > audio_threshold:
    print(f"音頻相似度: {similarity_score:.2f}")
    if text_similarity > text_threshold:
        print(f"文本相似度: {text_similarity:.2f}，完全相同")
    else:
        print(f"文本相似度: {text_similarity:.2f}，文本有差異")
        for tag, i1, i2, j1, j2 in diff_ops:
            if tag != 'equal':
                print(f"文本1: {' '.join(text1.split()[i1:i2])} | 文本2: {' '.join(text2.split()[j1:j2])}")
else:
    print(f"音頻相似度低，錯誤，相似度: {similarity_score:.2f}")
    if text_similarity > text_threshold:
        print(f"文本相似度: {text_similarity:.2f}，完全相同")
    else:
        print(f"文本相似度: {text_similarity:.2f}，文本有差異")
        for tag, i1, i2, j1, j2 in diff_ops:
            if tag != 'equal':
                print(f"文本1: {' '.join(text1.split()[i1:i2])} | 文本2: {' '.join(text2.split()[j1:j2])}")

print(f"文本1: {text1}")
print(f"文本2: {text2}")
