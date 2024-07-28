import os

# 列出當前工作目錄中的文件
current_directory = os.getcwd()
print(f"當前工作目錄: {current_directory}")

# 列出指定目錄中的文件
data_directory = os.path.join(current_directory, "mnt", "data")
print(f"數據目錄: {data_directory}")

if not os.path.exists(data_directory):
    print(f"數據目錄不存在: {data_directory}")
else:
    for root, dirs, files in os.walk(data_directory):
        for filename in files:
            print(os.path.join(root, filename))
