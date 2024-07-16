from gtts import gTTS
import os

def text_to_speech(text, save_path, language='zh-tw', voice_type='female'):
    if voice_type == 'female':
        tts = gTTS(text=text, lang=language, slow=False)
    elif voice_type == 'male':
        tts = gTTS(text=text, lang=language, slow=True)  # 模擬男性聲音的不同語速
    elif voice_type == 'robot':
        tts = gTTS(text=text, lang=language, slow=True)  # 模擬機器人聲音的不同語速
    else:
        raise ValueError("Invalid voice type. Choose from 'female', 'male', or 'robot'.")

    filename = f"{voice_type}_output.mp3"
    file_path = os.path.join(save_path, filename)
    tts.save(file_path)
    return file_path

#設定文字內容
text = "he's buried at the Union Cemetery in Billings Oklahoma"
#設定儲存路徑
save_path = r'C:\Users\ntubimd\Desktop\tts\mp3'
#確認路徑存在，不存在則創建
if not os.path.exists(save_path):
    os.makedirs(save_path)

#設定聲音類型
voice_types = ['female', 'male', 'robot']

#生成 MP3 檔案
for voice in voice_types:
    output_file = text_to_speech(text, save_path, voice_type=voice)
    print(f"生成的 MP3 檔案: {output_file}")