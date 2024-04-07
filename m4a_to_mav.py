from pydub import AudioSegment

# 定义输入文件名和输出文件名
input_file = '_9478149.m4a'
output_file = '_9478149.wav'

# 读取M4A文件
audio = AudioSegment.from_file(input_file, format="m4a")

# 将M4A文件保存为WAV文件
audio.export(output_file, format="wav")
