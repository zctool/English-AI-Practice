import speech_recognition as sr
r = sr.Recognizer()
WAV = sr.AudioFile('9ikn0-s53yn.wav')
with WAV as source:
    audio = r.record(source)
print(r.recognize_google(audio, show_all=True))

# import speech_recognition as sr

# # 建立Recognizer物件
# r = sr.Recognizer()

# # 讀取音訊檔案
# WAV = sr.AudioFile('ag7ut-ejpnc.wav')

# with WAV as source:
#     # 將音訊檔案轉換成音訊資料
#     audio = r.record(source)

# # 辨識音訊檔案中的語音內容
# try:
#     # 使用Google語音辨識API辨識音訊資料
#     result = r.recognize_google(audio, language='zh-TW')
#     print("辨識結果：", result)
# except sr.UnknownValueError:
#     print("無法辨識音訊")
# except sr.RequestError as e:
#     print("無法取得辨識服務：", e)
