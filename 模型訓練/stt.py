import os
from pydub import AudioSegment
import speech_recognition as sr
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import torch

# 明確指定ffmpeg和ffprobe的路徑
AudioSegment.converter = "C:/ffmpeg/bin/ffmpeg.exe"
AudioSegment.ffprobe = "C:/ffmpeg/bin/ffprobe.exe"

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

# 生成語音
def generate_speech(text, output_filename, model, tokenizer, device, torch_dtype):
    description = "A male teacher with a slightly low-pitched voice, in a very confined sounding environment with clear audio quality. He uses the voice for teaching propose."
    input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
    prompt_input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)
    generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids).to(torch.float32)
    audio_arr = generation.cpu().numpy().squeeze()
    sf.write(output_filename, audio_arr, model.config.sampling_rate)
    print(f"Generated {output_filename}")

# 主程序
if __name__ == "__main__":
    # 設置數據目錄
    data_directory = os.path.join(os.getcwd(), "data")

    # 設置設備
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    if torch.backends.mps.is_available():
        device = "mps"
    if torch.xpu.is_available():
        device = "xpu"

    print('device: ', device)
    torch_dtype = torch.float16 if device != "cpu" else torch.float32

    # 加載模型和標記器
    model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler_tts_mini_v0.1").to(device, dtype=torch_dtype)
    tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler_tts_mini_v0.1")

    # 進行語音轉文字並生成語音
    audio_files = [
        os.path.join(data_directory, f'common_voice_en_{i}.mp3') for i in range(11467,11467)
    ]

    for file in audio_files:
        text = speech_to_text(file)
        file_number = os.path.splitext(os.path.basename(file))[0].split('_')[-1]
        print(f"語音文件 {file_number} 的文字轉換結果:")
        print(text)
        
        if text:
            output_filename = os.path.join(data_directory, f"parler_tts_out_{file_number}.wav")
            generate_speech(text, output_filename, model, tokenizer, device, torch_dtype)

    print("所有音頻文件處理完成。")
