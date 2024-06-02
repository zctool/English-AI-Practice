import difflib
import re
from sentence_transformers import SentenceTransformer, util

# 加載SBERT模型
sbert_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def preprocess_text(text):
    # 移除標點符號並轉換為小寫
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower()

def highlight_differences(original_text, stt_text):
    original_text = preprocess_text(original_text)
    stt_text = preprocess_text(stt_text)
    
    original_tokens = original_text.split()
    stt_tokens = stt_text.split()
    
    diff = difflib.ndiff(original_tokens, stt_tokens)
    result = []

    for token in diff:
        if token.startswith('-'):
            result.append(f"<span style='color:green'>{token[2:]}</span>")
        elif token.startswith(' '):
            result.append(token[2:])
        elif token.startswith('+'):
            result.append(f"<span style='color:red'>{token[2:]}</span>")

    return ' '.join(result)

def calculate_accuracy(original_text, stt_text):
    original_text = preprocess_text(original_text)
    stt_text = preprocess_text(stt_text)
    
    # 使用SBERT计算相似度
    embeddings1 = sbert_model.encode(original_text, convert_to_tensor=True)
    embeddings2 = sbert_model.encode(stt_text, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embeddings1, embeddings2).item()
    return similarity

def process_texts(original_text, stt_text):
    highlighted_text = highlight_differences(original_text, stt_text)
    accuracy = calculate_accuracy(original_text, stt_text)
    return highlighted_text, accuracy
