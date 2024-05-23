import random
import mysql.connector
from flask import Flask, render_template, request, jsonify
import datetime
import base64

app = Flask(__name__)

# 数据库连接配置
db_config = {
    'user': 'case113201',
    'password': '@Ntub_113201',
    'host': '140.131.114.242',
    'database': '113-NTUB',
}

def get_random_conversations():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # 获取所有conversation的id
    cursor.execute("SELECT id FROM conversation")
    ids = [row['id'] for row in cursor.fetchall()]
    
    if len(ids) < 3:
        print("Not enough data in the database.")
        return []
    
    # 随机抽取三个id
    random_ids = random.sample(ids, 3)
    
    # 获取对应数据
    format_strings = ','.join(['%s'] * len(random_ids))
    cursor.execute(f"""
        SELECT 
            c.id,
            c.conversation_en, 
            c.conversation_tw, 
            c.conversation_voice,
            ch.character_name, 
            i.icon
        FROM conversation c
        JOIN characters ch ON c.character_id = ch.id
        JOIN icon i ON ch.icon_id = i.id
        WHERE c.id IN ({format_strings})
    """, random_ids)
    
    conversations = cursor.fetchall()
    
    for conversation in conversations:
        conversation['icon'] = base64.b64encode(conversation['icon']).decode('utf-8')
        conversation['conversation_voice'] = base64.b64encode(conversation['conversation_voice']).decode('utf-8')
    
    cursor.close()
    conn.close()
    
    print("Random Conversations:", conversations)
    return conversations

@app.route('/')
def index():
    conversations = get_random_conversations()
    if not conversations:
        return "No data available"
    return render_template('daily_quotes.html', conversations=conversations)

@app.route('/save_recording', methods=['POST'])
def save_recording():
    data = request.form
    user_voice = data['user_voice']
    stt = data['stt']
    conversation_id = data['conversation_id']
    user_email = '41327joseph@gmail.com'
    date_now = datetime.datetime.now().date()
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # 获取用户ID
    cursor.execute("SELECT id FROM users WHERE GoogleEmail = %s", (user_email,))
    user_id = cursor.fetchone()['id']
    
    # 检查是否存在相同的conversation_id和date记录
    cursor.execute("""
        SELECT id FROM conversationUserVoice
        WHERE conversation_id = %s AND user_id = %s AND date = %s
    """, (conversation_id, user_id, date_now))
    existing_record = cursor.fetchone()
    
    if existing_record:
        # 更新现有记录
        cursor.execute("""
            UPDATE conversationUserVoice
            SET user_voice = %s, STT = %s
            WHERE id = %s
        """, (base64.b64decode(user_voice), stt, existing_record['id']))
    else:
        # 插入新记录
        cursor.execute("""
            INSERT INTO conversationUserVoice (user_voice, STT, date, conversation_id, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (base64.b64decode(user_voice), stt, date_now, conversation_id, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
