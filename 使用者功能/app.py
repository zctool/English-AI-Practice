from flask import Flask, redirect, render_template, request, jsonify, url_for
import datetime
import base64
import random
from mysql.connector import pooling

app = Flask(__name__)

# 创建数据库连接池
db_config = {
    'user': 'case113201',
    'password': '@Ntub_113201',
    'host': '140.131.114.242',
    'database': '113-NTUB',
    'pool_name': 'mypool',
    'pool_size': 5
}

cnxpool = pooling.MySQLConnectionPool(**db_config)

def get_random_conversations():
    user_email = '41327joseph@gmail.com'
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 获取所有conversation的id
    cursor.execute("SELECT id FROM conversation")
    ids = [row['id'] for row in cursor.fetchall()]
    
    if len(ids) < 3:
        cursor.close()
        conn.close()
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
    
    # 获取用户ID
    cursor.execute("SELECT id FROM users WHERE GoogleEmail = %s", (user_email,))
    user_id = cursor.fetchone()['id']
    
    # 检查收藏状态
    for conversation in conversations:
        conversation_id = conversation['id']
        cursor.execute("""
            SELECT collect FROM conversationCollect
            WHERE user_id = %s AND conversation_id = %s
        """, (user_id, conversation_id))
        collect_record = cursor.fetchone()
        conversation['is_collected'] = collect_record['collect'] == 1 if collect_record else False
        conversation['icon'] = base64.b64encode(conversation['icon']).decode('utf-8')
        conversation['conversation_voice'] = base64.b64encode(conversation['conversation_voice']).decode('utf-8')
    
    cursor.close()
    conn.close()
    
    return conversations

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/daily_quotes')
def daily_quotes():
    conversations = get_random_conversations()
    if not conversations:
        return "No data available"
    return render_template('daily_quotes.html', conversations=conversations)

@app.route('/toggle_conversation_collect', methods=['POST'])
def toggle_conversation_collect():
    user_email = '41327joseph@gmail.com'
    conversation_id = request.form['conversation_id']
    collect = request.form['collect'] == 'true'
    
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 获取用户ID
    cursor.execute("SELECT id FROM users WHERE GoogleEmail = %s", (user_email,))
    user_id = cursor.fetchone()['id']
    
    # 检查是否存在收藏记录
    cursor.execute("""
        SELECT id FROM conversationCollect
        WHERE user_id = %s AND conversation_id = %s
    """, (user_id, conversation_id))
    collect_record = cursor.fetchone()
    
    if collect_record:
        # 更新现有记录
        cursor.execute("""
            UPDATE conversationCollect
            SET collect = %s
            WHERE id = %s
        """, (1 if collect else 0, collect_record['id']))
    else:
        # 插入新记录
        cursor.execute("""
            INSERT INTO conversationCollect (user_id, conversation_id, collect)
            VALUES (%s, %s, %s)
        """, (user_id, conversation_id, 1 if collect else 0))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success"})

# 新增单词练习功能的路由和处理逻辑

@app.route('/vocabulary_topics')
def vocabulary_topics():
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT vt.id, vt.name, vti.icon
        FROM vocabularyTopic vt
        JOIN vocabularyTopicIcon vti ON vt.id = vti.topic_id
    """)
    topics = cursor.fetchall()
    for topic in topics:
        topic['icon'] = base64.b64encode(topic['icon']).decode('utf-8')
    cursor.close()
    conn.close()
    return render_template('vocabulary_topics.html', topics=topics)

@app.route('/select_vocabulary', methods=['POST'])
def select_vocabulary():
    topic_id = request.form['topic_id']
    level = request.form['level']
    return redirect(url_for('vocabulary_list', topic_id=topic_id, level=level))

@app.route('/vocabulary_list/<int:topic_id>/<level>')
def vocabulary_list(topic_id, level):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, vocabulary_en, vocabulary_tw
        FROM vocabulary
        WHERE topic_id = %s AND class = %s
    """, (topic_id, level))
    vocabularies = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('vocabulary_list.html', vocabularies=vocabularies)

@app.route('/vocabulary_detail/<int:vocabulary_id>')
def vocabulary_detail(vocabulary_id):
    user_email = '41327joseph@gmail.com'  # 固定 GoogleEmail
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, vocabulary_voice, class
        FROM vocabulary
        WHERE id = %s
    """, (vocabulary_id,))
    vocabulary = cursor.fetchone()
    
    # 检查是否收藏
    cursor.execute("""
        SELECT collect FROM vocabularyCollect
        JOIN users ON users.id = vocabularyCollect.user_id
        WHERE users.GoogleEmail = %s AND vocabulary_id = %s
    """, (user_email, vocabulary_id))
    collect_record = cursor.fetchone()
    is_collected = collect_record['collect'] == 1 if collect_record else False
    
    vocabulary['vocabulary_voice'] = base64.b64encode(vocabulary['vocabulary_voice']).decode('utf-8')
    cursor.close()
    conn.close()
    return render_template('vocabulary_detail.html', vocabulary=vocabulary, is_collected=is_collected)

@app.route('/toggle_collect', methods=['POST'])
def toggle_collect():
    user_email = '41327joseph@gmail.com'
    vocabulary_id = request.form['vocabulary_id']
    collect = request.form['collect'] == 'true'
    
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 获取用户ID
    cursor.execute("SELECT id FROM users WHERE GoogleEmail = %s", (user_email,))
    user_id = cursor.fetchone()['id']
    
    # 检查是否存在收藏记录
    cursor.execute("""
        SELECT id FROM vocabularyCollect
        WHERE user_id = %s AND vocabulary_id = %s
    """, (user_id, vocabulary_id))
    collect_record = cursor.fetchone()
    
    if collect_record:
        # 更新现有记录
        cursor.execute("""
            UPDATE vocabularyCollect
            SET collect = %s
            WHERE id = %s
        """, (1 if collect else 0, collect_record['id']))
    else:
        # 插入新记录
        cursor.execute("""
            INSERT INTO vocabularyCollect (user_id, vocabulary_id, collect)
            VALUES (%s, %s, %s)
        """, (user_id, vocabulary_id, 1 if collect else 0))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
