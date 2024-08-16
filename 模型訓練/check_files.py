import os

# 列出當前工作目錄中的文件
current_directory = os.getcwd()
print(f"當前工作目錄: {current_directory}")

# 列出指定目錄中的文件
data_directory = os.path.join(current_directory, "mnt", "data")
print(f"數據目錄: {data_directory}")

# 初始化一个列表来存储音频文件路径
audio_files = []

if not os.path.exists(data_directory):
    print(f"數據目錄不存在: {data_directory}")
else:
    for root, dirs, files in os.walk(data_directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            print(file_path)
            # 只添加 .wav 文件到列表
            if filename.endswith(".wav"):
                audio_files.append(file_path)

# 打印所有找到的音频文件路径
print("\n找到的音频文件路径:")
for file in audio_files:
    print(file)
