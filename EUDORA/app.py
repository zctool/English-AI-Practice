import os
import base64
import datetime
import random
import time
import tempfile
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from mysql.connector import pooling, Error
import requests
from ai_comparison import process_texts  # 導入文件處理模型
from teacher import teacher_bp
from admin import admin_bp  # 導入管理者藍圖
import speech_recognition as sr
from pyannote.audio import Model, Inference
from scipy.spatial.distance import cosine
from difflib import SequenceMatcher
from pydub import AudioSegment
import io
import json


app = Flask(__name__)
app.secret_key = os.urandom(24)

# 創建資料庫連接池
db_config = {
    'user': 'eudora',
    'password': '',
    'host': '20.18.40.160',
    'database': '113-ntub',
    'pool_name': 'mypool',
    'pool_size': 5
}

def get_connection(retry_count=3):
    attempt = 0
    while attempt < retry_count:
        try:
            return pooling.MySQLConnectionPool(**db_config)
        except Error as e:
            attempt += 1
            time.sleep(1)  # 等待一秒後重試
            if attempt == retry_count:
                raise e

cnxpool = get_connection()

def execute_query(query, params=None, retry_count=3):
    attempt = 0
    while attempt < retry_count:
        try:
            conn = cnxpool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.commit()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            attempt += 1
            time.sleep(1)  # 等待一秒後重試
            if attempt == retry_count:
                raise e

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('main'))
    return render_template('index.html')

@app.route('/login/callback', methods=['POST'])
def callback():
    token = request.json.get('id_token')
    userinfo_response = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": token}
    )
    userinfo = userinfo_response.json()

    if userinfo.get('email_verified'):
        users_email = userinfo['email']
        users_name = userinfo['name']
        picture = userinfo['picture']

        session['email'] = users_email
        session['name'] = users_name

        conn = cnxpool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE GoogleEmail = %s", (users_email,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({'register_required': True})

        cursor.execute("SELECT role FROM users WHERE GoogleEmail = %s", (users_email,))
        user = cursor.fetchone()
        session['role'] = user['role']

        cursor.close()
        conn.close()

        if session['role'] == 'admin':
            return jsonify({'redirect_url': url_for('admin.admin_index')})
        elif session['role'] == 'teacher':
            return jsonify({'redirect_url': url_for('teacher.teacher_index')})
        else:
            return jsonify({'redirect_url': url_for('main')})
    else:
        return jsonify({'error': '用戶身份驗證失敗'}), 400

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    icon = request.files['icon'].read() if 'icon' in request.files else None

    conn = cnxpool.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (userName, GoogleEmail, icon, role) VALUES (%s, %s, %s, 'user')", (username, email, icon))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('main'))

@app.route('/main')
def main():
    if 'email' not in session:
        return redirect(url_for('index'))

    user_email = session['email']
    user = execute_query("SELECT userName, role FROM users WHERE GoogleEmail = %s", (user_email,))[0]

    if user['role'] == 'admin':
        return redirect(url_for('admin.admin_index'))
    elif user['role'] == 'teacher':
        return redirect(url_for('teacher.teacher_index'))
    else:
        return render_template('main.html', name=user['userName'], email=user_email)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 獲取用戶ID
def get_user_id(email):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE GoogleEmail = %s", (email,))
    user_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return user_id

# 獲取原始文本
def get_original_text_by_vocabulary_id(vocabulary_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT vocabulary_en FROM vocabulary WHERE id = %s", (vocabulary_id,))
    original_text = cursor.fetchone()['vocabulary_en']
    cursor.close()
    conn.close()
    return original_text

def get_original_text_by_conversation_id(conversation_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT conversation_en FROM conversation WHERE id = %s", (conversation_id,))
    original_text = cursor.fetchone()['conversation_en']
    cursor.close()
    conn.close()
    return original_text

# 每日三句頁面
@app.route('/daily_quotes')
def daily_quotes():
    user_email = session['email']
    conversations = get_random_conversations(user_email)
    if not conversations:
        return "No data available"
    return render_template('daily_quotes.html', conversations=conversations)

# 隨機獲取三個對話並檢查收藏狀態
def get_random_conversations(user_email):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 獲取所有conversation的id
    cursor.execute("SELECT id FROM conversation")
    ids = [row['id'] for row in cursor.fetchall()]
    
    if len(ids) < 3:
        cursor.close()
        conn.close()
        return []
    
    # 隨機抽取三個id
    random_ids = random.sample(ids, 3)
    
    # 獲取對應數據
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
    
    user_id = get_user_id(user_email)
    
    # 檢查收藏狀態
    for conversation in conversations:
        conversation_id = conversation['id']
        cursor.execute("""
            SELECT 1 FROM conversationCollect
            WHERE user_id = %s AND conversation_id = %s
        """, (user_id, conversation_id))
        collect_record = cursor.fetchone()
        conversation['is_collected'] = collect_record is not None
        conversation['icon'] = base64.b64encode(conversation['icon']).decode('utf-8')
        conversation['conversation_voice'] = base64.b64encode(conversation['conversation_voice']).decode('utf-8')
    
    cursor.close()
    conn.close()
    
    return conversations

# 切換對話收藏狀態
@app.route('/toggle_conversation_collect', methods=['POST'])
def toggle_conversation_collect():
    user_email = session['email']
    conversation_id = request.form['conversation_id']
    
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    user_id = get_user_id(user_email)
    
    # 檢查是否存在收藏記錄
    cursor.execute("""
        SELECT id FROM conversationCollect
        WHERE user_id = %s AND conversation_id = %s
    """, (user_id, conversation_id))
    collect_record = cursor.fetchone()
    
    if collect_record:
        # 刪除現有記錄
        cursor.execute("""
            DELETE FROM conversationCollect
            WHERE id = %s
        """, (collect_record['id'],))
    else:
        # 插入新記錄
        cursor.execute("""
            INSERT INTO conversationCollect (user_id, conversation_id)
            VALUES (%s, %s)
        """, (user_id, conversation_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success"})

# 單字主題頁面
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
    
    # 添加調試信息
    print("Topics fetched from database:", topics)
    
    for topic in topics:
        topic['icon'] = base64.b64encode(topic['icon']).decode('utf-8')
        
    cursor.close()
    conn.close()
    
    # 再次添加調試信息
    print("Topics after encoding:", topics)
    
    return render_template('vocabulary_topics.html', topics=topics)

# 選擇單字主題和難度
@app.route('/select_vocabulary', methods=['POST'])
def select_vocabulary():
    topic_id = request.form['topic_id']
    level = request.form['level']
    return redirect(url_for('vocabulary_list', topic_id=topic_id, level=level))

# 單字列表頁面
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

# 單字詳細頁面
@app.route('/vocabulary_detail/<int:vocabulary_id>')
def vocabulary_detail(vocabulary_id):
    user_email = session['email']
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 查詢單字詳細信息
    cursor.execute("""
        SELECT id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, vocabulary_voice, class
        FROM vocabulary
        WHERE id = %s
    """, (vocabulary_id,))
    vocabulary = cursor.fetchone()
    
    # 檢查是否收藏
    cursor.execute("""
        SELECT 1 FROM vocabularyCollect
        JOIN users ON users.id = vocabularyCollect.user_id
        WHERE users.GoogleEmail = %s AND vocabulary_id = %s
    """, (user_email, vocabulary_id))
    collect_record = cursor.fetchone()
    is_collected = collect_record is not None
    
    # 將音頻轉為 base64 格式
    vocabulary['vocabulary_voice'] = base64.b64encode(vocabulary['vocabulary_voice']).decode('utf-8')
    
    # 獲取用戶錄音比對結果
    cursor.execute("""
        SELECT STT, accuracy, highlighted_text
        FROM vocabularyUserVoice
        WHERE user_id = %s AND vocabulary_id = %s
        ORDER BY date DESC
        LIMIT 1
    """, (get_user_id(user_email), vocabulary_id))
    user_voice = cursor.fetchone()
    
    # 如果有比對結果，格式化準確率
    if user_voice:
        user_voice['accuracy'] = f"{round(user_voice['accuracy'], 2):.2f}"

    # 如果沒有比對結果，設置為空字典
    if not user_voice:
        user_voice = {'STT': '', 'accuracy': '', 'highlighted_text': ''}

    cursor.close()
    conn.close()

    return render_template('vocabulary_detail.html', vocabulary=vocabulary, is_collected=is_collected, user_voice=user_voice)

# 切換單字收藏狀態
@app.route('/toggle_vocabulary_collect', methods=['POST'])
def toggle_vocabulary_collect():
    user_email = session['email']
    vocabulary_id = request.form['vocabulary_id']

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = get_user_id(user_email)

    # 檢查是否存在收藏記錄
    cursor.execute("""
        SELECT id FROM vocabularyCollect
        WHERE user_id = %s AND vocabulary_id = %s
    """, (user_id, vocabulary_id))
    collect_record = cursor.fetchone()

    if collect_record:
        # 刪除現有記錄
        cursor.execute("""
            DELETE FROM vocabularyCollect
            WHERE id = %s
        """, (collect_record['id'],))
    else:
        # 插入新記錄
        cursor.execute("""
            INSERT INTO vocabularyCollect (user_id, vocabulary_id)
            VALUES (%s, %s)
        """, (user_id, vocabulary_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

#對話主題
@app.route('/conversation_topics')
def conversation_topics():
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 獲取所有對話主題及其圖標
    cursor.execute("""
        SELECT vt.id, vt.name, vti.icon
        FROM conversationTopic vt
        JOIN conversationTopicIcon vti ON vt.id = vti.topic_id
    """)
    topics = cursor.fetchall()
    
    # 根據每個主題，獲取其難易度
    for topic in topics:
        cursor.execute("""
            SELECT DISTINCT class 
            FROM conversationSituation 
            WHERE topic_id = %s
        """, (topic['id'],))
        difficulties = [row['class'] for row in cursor.fetchall()]
        topic['difficulties'] = difficulties
        topic['icon'] = base64.b64encode(topic['icon']).decode('utf-8')
    
    cursor.close()
    conn.close()
    return render_template('conversation_topics.html', topics=topics)

#對話情境
@app.route('/conversation_situations/<int:topic_id>/<difficulty>')
def conversation_situations(topic_id, difficulty):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, situation 
        FROM conversationSituation 
        WHERE topic_id = %s AND class = %s
    """, (topic_id, difficulty))
    
    situations = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('conversation_situations.html', topic_id=topic_id, situations=situations, difficulty=difficulty)

#對話練習
@app.route('/conversation_practice/<int:topic_id>/<difficulty>/<int:situation_id>')
def conversation_practice(topic_id, difficulty, situation_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            c.id, c.conversation_en, c.conversation_tw, c.conversation_voice,
            ch.character_name, i.icon
        FROM conversation c
        JOIN characters ch ON c.character_id = ch.id
        JOIN icon i ON ch.icon_id = i.id
        WHERE c.situation_id = %s
        ORDER BY c.id ASC
    """, (situation_id,))
    conversations = cursor.fetchall()
    
    user_email = session['email']
    user_id = get_user_id(user_email)
    
    for conversation in conversations:
        conversation_id = conversation['id']
        cursor.execute("""
            SELECT 1 FROM conversationCollect
            WHERE user_id = %s AND conversation_id = %s
        """, (user_id, conversation_id))
        collect_record = cursor.fetchone()
        conversation['is_collected'] = collect_record is not None
        conversation['icon'] = base64.b64encode(conversation['icon']).decode('utf-8')
        conversation['conversation_voice'] = base64.b64encode(conversation['conversation_voice']).decode('utf-8')
    
    cursor.close()
    conn.close()
    
    return render_template('conversation_practice.html', conversations=conversations, topic_id=topic_id, difficulty=difficulty, situation_id=situation_id)

# 保存對話錄音
@app.route('/save_recording', methods=['POST'])
def save_recording():
    data = request.form
    user_voice = data['user_voice']
    stt = data['stt']
    conversation_id = data.get('conversation_id')  # 對話錄音
    user_email = session['email']
    date_now = datetime.datetime.now().date()

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 獲取用戶ID
    user_id = get_user_id(user_email)

    if conversation_id:
        # 獲取原始文本
        original_text = get_original_text_by_conversation_id(conversation_id)
        # 處理文本，計算準確率
        highlighted_text, accuracy = process_texts(original_text, stt)
        accuracy *= 100  # 正確率乘以100
        # 更新或插入錄音記錄到 conversationUserVoice 表
        cursor.execute("""
            INSERT INTO conversationUserVoice (user_voice, STT, date, conversation_id, user_id, highlighted_text, accuracy)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE user_voice = VALUES(user_voice), STT = VALUES(STT), highlighted_text = VALUES(highlighted_text), accuracy = VALUES(accuracy)
        """, (base64.b64decode(user_voice), stt, date_now, conversation_id, user_id, highlighted_text, accuracy))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success", "stt": stt, "accuracy": accuracy, "highlighted_text": highlighted_text})

# 保存單字錄音
@app.route('/save_vocabulary_recording', methods=['POST'])
def save_vocabulary_recording():
    user_voice = request.form['user_voice']
    stt = request.form['stt']
    vocabulary_id = request.form['vocabulary_id']
    user_email = session['email']
    date_now = datetime.datetime.now().date()

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 獲取用戶ID
    user_id = get_user_id(user_email)

    # 獲取原始文本
    original_text = get_original_text_by_vocabulary_id(vocabulary_id)

    # 處理文本，計算準確率
    highlighted_text, accuracy = process_texts(original_text, stt)
    accuracy *= 100  # 正確率乘以100

    # 更新或插入錄音記錄到 vocabularyUserVoice 表
    cursor.execute("""
        INSERT INTO vocabularyUserVoice (user_voice, STT, date, vocabulary_id, user_id, highlighted_text, accuracy)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE user_voice = VALUES(user_voice), STT = VALUES(STT), highlighted_text = VALUES(highlighted_text), accuracy = VALUES(accuracy)
    """, (base64.b64decode(user_voice), stt, date_now, vocabulary_id, user_id, highlighted_text, accuracy))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success", "stt": stt, "accuracy": accuracy, "highlighted_text": highlighted_text})

# 學習歷程 - 單字
@app.route('/learning_history_vocabulary', methods=['GET', 'POST'])
def learning_history_vocabulary():
    user_email = session['email']
    user_id = get_user_id(user_email)
    date_filter = request.form.get('date_filter', None)

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if date_filter:
        cursor.execute("""
            SELECT v.id, v.vocabulary_en, v.vocabulary_tw, v.vocabulary_voice, vuv.user_voice, vuv.STT, vuv.date, vuv.highlighted_text, vuv.accuracy,
                   IF(vc.id IS NOT NULL, TRUE, FALSE) AS is_collected
            FROM vocabularyUserVoice vuv
            JOIN vocabulary v ON vuv.vocabulary_id = v.id
            LEFT JOIN vocabularyCollect vc ON vuv.vocabulary_id = vc.vocabulary_id AND vuv.user_id = vc.user_id
            WHERE vuv.user_id = %s AND vuv.date = %s
            ORDER BY vuv.date ASC
        """, (user_id, date_filter))
    else:
        cursor.execute("""
            SELECT v.id, v.vocabulary_en, v.vocabulary_tw, v.vocabulary_voice, vuv.user_voice, vuv.STT, vuv.date, vuv.highlighted_text, vuv.accuracy,
                   IF(vc.id IS NOT NULL, TRUE, FALSE) AS is_collected
            FROM vocabularyUserVoice vuv
            JOIN vocabulary v ON vuv.vocabulary_id = v.id
            LEFT JOIN vocabularyCollect vc ON vuv.vocabulary_id = vc.vocabulary_id AND vuv.user_id = vc.user_id
            WHERE vuv.user_id = %s
            ORDER BY vuv.date ASC
        """, (user_id,))
    
    learning_history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for record in learning_history:
        if record['vocabulary_voice'] is not None:
            record['vocabulary_voice'] = base64.b64encode(record['vocabulary_voice']).decode('utf-8')
        if record['user_voice'] is not None:
            record['user_voice'] = base64.b64encode(record['user_voice']).decode('utf-8')
    
    return render_template('learning_history_vocabulary.html', learning_history=learning_history, date_filter=date_filter)

# 切換收藏狀態 - 學習歷程單字
@app.route('/toggle_learning_history_vocabulary_collect', methods=['POST'])
def toggle_learning_history_vocabulary_collect():
    user_email = session['email']
    vocabulary_id = request.form['vocabulary_id']

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = get_user_id(user_email)

    # 檢查是否存在收藏記錄
    cursor.execute("""
        SELECT id FROM vocabularyCollect
        WHERE user_id = %s AND vocabulary_id = %s
    """, (user_id, vocabulary_id))
    collect_record = cursor.fetchone()

    if collect_record:
        # 刪除現有記錄
        cursor.execute("""
            DELETE FROM vocabularyCollect
            WHERE id = %s
        """, (collect_record['id'],))
    else:
        # 插入新記錄
        cursor.execute("""
            INSERT INTO vocabularyCollect (user_id, vocabulary_id)
            VALUES (%s, %s)
        """, (user_id, vocabulary_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

# 學習歷程 - 對話
@app.route('/learning_history_conversation', methods=['GET', 'POST'])
def learning_history_conversation():
    user_email = session['email']
    user_id = get_user_id(user_email)
    date_filter = request.form.get('date_filter', None)

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if date_filter:
        cursor.execute("""
            SELECT c.id, c.conversation_en, c.conversation_tw, c.conversation_voice, cuv.user_voice, cuv.STT, cuv.date, cuv.highlighted_text, cuv.accuracy,
                   IF(cc.id IS NOT NULL, TRUE, FALSE) AS is_collected
            FROM conversationUserVoice cuv
            JOIN conversation c ON cuv.conversation_id = c.id
            LEFT JOIN conversationCollect cc ON cuv.conversation_id = cc.conversation_id AND cuv.user_id = cc.user_id
            WHERE cuv.user_id = %s AND cuv.date = %s
            ORDER BY cuv.date ASC
        """, (user_id, date_filter))
    else:
        cursor.execute("""
            SELECT c.id, c.conversation_en, c.conversation_tw, c.conversation_voice, cuv.user_voice, cuv.STT, cuv.date, cuv.highlighted_text, cuv.accuracy,
                   IF(cc.id IS NOT NULL, TRUE, FALSE) AS is_collected
            FROM conversationUserVoice cuv
            JOIN conversation c ON cuv.conversation_id = c.id
            LEFT JOIN conversationCollect cc ON cuv.conversation_id = cc.conversation_id AND cuv.user_id = cc.user_id
            WHERE cuv.user_id = %s
            ORDER BY cuv.date ASC
        """, (user_id,))
    
    learning_history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for record in learning_history:
        record['conversation_voice'] = base64.b64encode(record['conversation_voice']).decode('utf-8')
        record['user_voice'] = base64.b64encode(record['user_voice']).decode('utf-8')
    
    return render_template('learning_history_conversation.html', learning_history=learning_history, date_filter=date_filter)

# 帳號管理頁面
@app.route('/account_management', methods=['GET', 'POST'])
def account_management():
    user_email = session.get('email')

    if request.method == 'POST':
        # 獲取提交的資料
        user_name = request.form['userName']
        icon_file = request.files['icon']
        icon_data = icon_file.read() if icon_file else None

        conn = cnxpool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # 更新用戶資料
        update_query = "UPDATE users SET userName = %s"
        update_data = [user_name]

        if icon_data:
            update_query += ", icon = %s"
            update_data.append(icon_data)

        update_query += " WHERE GoogleEmail = %s"
        update_data.append(user_email)

        cursor.execute(update_query, update_data)
        conn.commit()
        
        # 更新 session 中的名稱
        session['name'] = user_name

        cursor.close()
        conn.close()

    # 獲取當前用戶資料
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT userName, GoogleEmail, icon FROM users WHERE GoogleEmail = %s", (user_email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # 將圖片轉為 base64 格式
    if user['icon']:
        user['icon'] = base64.b64encode(user['icon']).decode('utf-8')

    return render_template('account_management.html', user=user)

# 帳號管理頁面
@app.route('/account_manage', methods=['GET', 'POST'])
def account_manage():
    user_email = session.get('email')

    if request.method == 'POST':
        # 獲取提交的資料
        user_name = request.form['userName']
        icon_file = request.files['icon']
        icon_data = icon_file.read() if icon_file else None

        conn = cnxpool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # 更新用戶資料
        update_query = "UPDATE users SET userName = %s"
        update_data = [user_name]

        if icon_data:
            update_query += ", icon = %s"
            update_data.append(icon_data)

        update_query += " WHERE GoogleEmail = %s"
        update_data.append(user_email)

        cursor.execute(update_query, update_data)
        conn.commit()
        
        # 更新 session 中的名稱
        session['name'] = user_name

        cursor.close()
        conn.close()

    # 獲取當前用戶資料
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT userName, GoogleEmail, icon FROM users WHERE GoogleEmail = %s", (user_email,))  # 替换成 GoogleEmail
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # 將圖片轉為 base64 格式
    if user['icon']:
        user['icon'] = base64.b64encode(user['icon']).decode('utf-8')

    return render_template('account_manage.html', user=user)
#學習月曆
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

# 獲取每一天的練習次數
@app.route('/api/daily_counts')
def api_daily_counts():
    month = int(request.args.get('month'))
    year = int(request.args.get('year'))
    user_email = session.get('email')
    
    if not user_email:
        return jsonify({})
    
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 獲取用戶ID
    cursor.execute("SELECT id FROM users WHERE GoogleEmail = %s", (user_email,))
    user_id = cursor.fetchone()['id']
    
    # 獲取該用戶在指定月份的練習次數
    query = """
    SELECT DATE(date) as practice_date, 
           COUNT(DISTINCT CASE WHEN conversation_id IS NOT NULL THEN id END) as conversations,
           COUNT(DISTINCT CASE WHEN vocabulary_id IS NOT NULL THEN id END) as vocabularies
    FROM (
        SELECT id, date, conversation_id, NULL as vocabulary_id
        FROM conversationUserVoice
        WHERE user_id = %s AND YEAR(date) = %s AND MONTH(date) = %s
        UNION ALL
        SELECT id, date, NULL as conversation_id, vocabulary_id
        FROM vocabularyUserVoice
        WHERE user_id = %s AND YEAR(date) = %s AND MONTH(date) = %s
    ) as combined
    GROUP BY practice_date
    """
    
    cursor.execute(query, (user_id, year, month, user_id, year, month))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    daily_counts = {result['practice_date'].strftime('%Y-%m-%d'): {
        'conversations': result['conversations'],
        'vocabularies': result['vocabularies']
    } for result in results}
    
    return jsonify(daily_counts)

# 學習筆記 - 對話收藏
@app.route('/learning_notes_conversation')
def learning_notes_conversation():
    user_email = session['email']
    user_id = get_user_id(user_email)
    
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 獲取用戶收藏的對話
    cursor.execute("""
        SELECT 
            c.id, c.conversation_en, c.conversation_tw, c.conversation_voice,
            ch.character_name, i.icon, cuv.user_voice, cuv.STT, cuv.accuracy, cuv.highlighted_text,
            IF(cc.id IS NOT NULL, TRUE, FALSE) AS is_collected
        FROM conversationCollect cc
        JOIN conversation c ON cc.conversation_id = c.id
        JOIN characters ch ON c.character_id = ch.id
        JOIN icon i ON ch.icon_id = i.id
        LEFT JOIN conversationUserVoice cuv ON c.id = cuv.conversation_id AND cc.user_id = cuv.user_id
        WHERE cc.user_id = %s
        ORDER BY c.id ASC
    """, (user_id,))
    
    conversations = cursor.fetchall()
    
    for conversation in conversations:
        conversation['icon'] = base64.b64encode(conversation['icon']).decode('utf-8')
        conversation['conversation_voice'] = base64.b64encode(conversation['conversation_voice']).decode('utf-8')
        if conversation['user_voice'] is not None:
            conversation['user_voice'] = base64.b64encode(conversation['user_voice']).decode('utf-8')
        # 確保 accuracy 不是空值
        if conversation['accuracy'] is None:
            conversation['accuracy'] = 0.0
    
    cursor.close()
    conn.close()
    
    return render_template('learning_notes_conversation.html', conversations=conversations)

# 學習筆記 - 單字收藏
@app.route('/learning_notes_vocabulary')
def learning_notes_vocabulary():
    user_email = session['email']
    user_id = get_user_id(user_email)
    
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 獲取用戶收藏的單字
    cursor.execute("""
        SELECT 
            v.id, v.vocabulary_en, v.vocabulary_tw, v.part_of_speech, v.ipa, 
            v.example, v.vocabulary_voice, vt.name as topic_name, vuv.user_voice, vuv.STT, vuv.accuracy, vuv.highlighted_text,
            IF(vc.id IS NOT NULL, TRUE, FALSE) AS is_collected
        FROM vocabularyCollect vc
        JOIN vocabulary v ON vc.vocabulary_id = v.id
        JOIN vocabularyTopic vt ON v.topic_id = vt.id
        LEFT JOIN vocabularyUserVoice vuv ON v.id = vuv.vocabulary_id AND vc.user_id = vuv.user_id
        WHERE vc.user_id = %s
        ORDER BY v.id ASC
    """, (user_id,))
    
    vocabularies = cursor.fetchall()
    
    for vocabulary in vocabularies:
        vocabulary['vocabulary_voice'] = base64.b64encode(vocabulary['vocabulary_voice']).decode('utf-8')
        if vocabulary['user_voice'] is not None:
            vocabulary['user_voice'] = base64.b64encode(vocabulary['user_voice']).decode('utf-8')
        # 確保 accuracy 不是空值
        if vocabulary['accuracy'] is None:
            vocabulary['accuracy'] = 0.0
    
    cursor.close()
    conn.close()
    
    return render_template('learning_notes_vocabulary.html', vocabularies=vocabularies)

# 切換收藏狀態 - 對話
@app.route('/toggle_learning_notes_conversation_collect', methods=['POST'])
def toggle_learning_notes_conversation_collect():
    user_email = session['email']
    conversation_id = request.form['conversation_id']

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = get_user_id(user_email)

    # 檢查是否存在收藏記錄
    cursor.execute("""
        SELECT id FROM conversationCollect
        WHERE user_id = %s AND conversation_id = %s
    """, (user_id, conversation_id))
    collect_record = cursor.fetchone()

    if collect_record:
        # 刪除現有記錄
        cursor.execute("""
            DELETE FROM conversationCollect
            WHERE id = %s
        """, (collect_record['id'],))
    else:
        # 插入新記錄
        cursor.execute("""
            INSERT INTO conversationCollect (user_id, conversation_id)
            VALUES (%s, %s)
        """, (user_id, conversation_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

# 切換收藏狀態 - 單字
@app.route('/toggle_learning_notes_vocabulary_collect', methods=['POST'])
def toggle_learning_notes_vocabulary_collect():
    user_email = session['email']
    vocabulary_id = request.form['vocabulary_id']

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = get_user_id(user_email)

    # 檢查是否存在收藏記錄
    cursor.execute("""
        SELECT id FROM vocabularyCollect
        WHERE user_id = %s AND vocabulary_id = %s
    """, (user_id, vocabulary_id))
    collect_record = cursor.fetchone()

    if collect_record:
        # 刪除現有記錄
        cursor.execute("""
            DELETE FROM vocabularyCollect
            WHERE id = %s
        """, (collect_record['id'],))
    else:
        # 插入新記錄
        cursor.execute("""
            INSERT INTO vocabularyCollect (user_id, vocabulary_id)
            VALUES (%s, %s)
        """, (user_id, vocabulary_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

# 檢查文件類型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

## 所有老師列表
@app.route('/all_teachers', methods=['GET', 'POST'])
def all_teachers():
    search_query = request.form.get('search', '')

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    user_id = get_user_id(session['email'])
    
    if search_query:
        cursor.execute("""
            SELECT u.id, u.userName AS name, 
            CASE 
                WHEN tf.id IS NOT NULL THEN 1 
                ELSE 0 
            END AS is_favorite 
            FROM users u
            LEFT JOIN teacher_favorites tf ON u.id = tf.teacher_id AND tf.user_id = %s
            WHERE u.role = 'teacher' AND u.userName LIKE %s
        """, (user_id, '%' + search_query + '%'))
    else:
        cursor.execute("""
            SELECT u.id, u.userName AS name, 
            CASE 
                WHEN tf.id IS NOT NULL THEN 1 
                ELSE 0 
            END AS is_favorite 
            FROM users u
            LEFT JOIN teacher_favorites tf ON u.id = tf.teacher_id AND tf.user_id = %s
            WHERE u.role = 'teacher'
        """, (user_id,))
    
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('all_teachers.html', teachers=teachers, search_query=search_query)


# 獲取推薦的老師列表
@app.route('/recommended_teachers', methods=['GET', 'POST'])
def recommended_teachers():
    search_query = request.form.get('search', '')

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    user_id = get_user_id(session['email'])
    
    if search_query:
        cursor.execute("""
            SELECT u.id, u.userName AS name, 
            CASE 
                WHEN MAX(tf.id) IS NOT NULL THEN 1 
                ELSE 0 
            END AS is_favorite 
            FROM users u
            LEFT JOIN teacher_favorites tf ON u.id = tf.teacher_id AND tf.user_id = %s
            JOIN Course c ON u.GoogleEmail = c.teacher_email
            WHERE u.role = 'teacher' AND u.userName LIKE %s
            GROUP BY u.id 
            ORDER BY COUNT(c.id) DESC
        """, (user_id, '%' + search_query + '%'))
    else:
        cursor.execute("""
            SELECT u.id, u.userName AS name, 
            CASE 
                WHEN MAX(tf.id) IS NOT NULL THEN 1 
                ELSE 0 
            END AS is_favorite 
            FROM users u
            LEFT JOIN teacher_favorites tf ON u.id = tf.teacher_id AND tf.user_id = %s
            JOIN Course c ON u.GoogleEmail = c.teacher_email
            WHERE u.role = 'teacher'
            GROUP BY u.id 
            ORDER BY COUNT(c.id) DESC
        """, (user_id,))
    
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('recommended_teachers.html', teachers=teachers, search_query=search_query)


# 獲取已選擇過的老師列表
@app.route('/selected_teachers', methods=['GET', 'POST'])
def selected_teachers():
    user_email = session['email']
    search_query = request.form.get('search', '')

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    user_id = get_user_id(user_email)
    
    if search_query:
        cursor.execute("""
            SELECT DISTINCT u.id, u.userName AS name, 
            CASE 
                WHEN tf.id IS NOT NULL THEN 1 
                ELSE 0 
            END AS is_favorite 
            FROM users u
            LEFT JOIN teacher_favorites tf ON u.id = tf.teacher_id AND tf.user_id = %s
            JOIN teacher_favorites tf2 ON tf2.teacher_id = u.id
            WHERE tf2.user_id = %s AND u.role = 'teacher' AND u.userName LIKE %s
        """, (user_id, user_id, '%' + search_query + '%'))
    else:
        cursor.execute("""
            SELECT DISTINCT u.id, u.userName AS name, 
            CASE 
                WHEN tf.id IS NOT NULL THEN 1 
                ELSE 0 
            END AS is_favorite 
            FROM users u
            LEFT JOIN teacher_favorites tf ON u.id = tf.teacher_id AND tf.user_id = %s
            JOIN teacher_favorites tf2 ON tf2.teacher_id = u.id
            WHERE tf2.user_id = %s AND u.role = 'teacher'
        """, (user_id, user_id))
    
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('selected_teachers.html', teachers=teachers, search_query=search_query)


# 檢查用戶是否收藏了該老師
def check_if_favorite_teacher(teacher_id):
    user_email = session['email']
    user_id = get_user_id(user_email)

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 檢查是否收藏了老師
    cursor.execute("""
        SELECT 1 FROM teacher_favorites 
        WHERE user_id = %s AND teacher_id = %s
    """, (user_id, teacher_id))
    favorite = cursor.fetchone()

    cursor.close()
    conn.close()

    return favorite is not None

@app.route('/toggle_teacher_favorite', methods=['POST'])
def toggle_teacher_favorite():
    teacher_id = request.json.get('teacher_id')
    user_email = session['email']
    user_id = get_user_id(user_email)

    conn = cnxpool.get_connection()
    cursor = conn.cursor()

    # 输出调试信息
    print(f"Toggling favorite for user {user_id} and teacher {teacher_id}")

    if check_if_favorite_teacher(teacher_id):
        # 取消收藏
        cursor.execute("""
            DELETE FROM teacher_favorites 
            WHERE user_id = %s AND teacher_id = %s
        """, (user_id, teacher_id))
        print(f"取消收藏: user {user_id}, teacher {teacher_id}")
    else:
        # 收藏老師
        cursor.execute("""
            INSERT INTO teacher_favorites (user_id, teacher_id)
            VALUES (%s, %s)
        """, (user_id, teacher_id))
        print(f"收藏老師: user {user_id}, teacher {teacher_id}")

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

# 查看老師的課程
@app.route('/view_courses_by_teacher/<int:teacher_id>')
def view_courses_by_teacher(teacher_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 通過老師的 email 來查詢課程，並且只顯示is_open為True的課程
    cursor.execute("""
        SELECT id, name 
        FROM Course 
        WHERE teacher_email = (SELECT GoogleEmail FROM users WHERE id = %s) AND is_open = TRUE
    """, (teacher_id,))
    courses = cursor.fetchall()
    
    for course in courses:
        course['is_favorite'] = check_if_favorite_teacher(teacher_id)  # 傳遞是否收藏的信息

    cursor.close()
    conn.close()

    return render_template('teacher_courses.html', courses=courses)

# 查看課程詳情
@app.route('/view_course_detail/<int:course_id>')
def view_course_detail(course_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 獲取課程的詳細信息
    cursor.execute("SELECT * FROM Course WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    
    if course['type'] == 'conversation':
        # 獲取對話類型課程的句子和音頻信息
        cursor.execute("SELECT content AS text, audio_file FROM Sentence WHERE course_id = %s", (course_id,))
        course['sentences'] = cursor.fetchall()
        
        # 將音頻文件轉換成 base64 格式
        for sentence in course['sentences']:
            sentence['audio_file'] = base64.b64encode(sentence['audio_file']).decode('utf-8')
            
    else:
        # 對於文章類型課程，獲取內容信息
        cursor.execute("SELECT content AS text, audio_file FROM Sentence WHERE course_id = %s", (course_id,))
        course['content'] = cursor.fetchall()
        
        # 將音頻文件轉換成 base64 格式
        for paragraph in course['content']:
            paragraph['audio_file'] = base64.b64encode(paragraph['audio_file']).decode('utf-8')
    
    cursor.close()
    conn.close()
    return render_template('course_detail.html', course=course)

# 音頻保存為 wav 格式
def save_audio_as_wav(file_data, output_path):
    try:
        audio = AudioSegment.from_file(io.BytesIO(file_data))
        audio.export(output_path, format="wav")
        print(f"Audio saved successfully at {output_path}")
    except Exception as e:
        print(f"Error saving audio: {e}")

# 音頻識別
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

# 提取音頻嵌入
def extract_audio_embedding(file_path):
    model = Model.from_pretrained("pyannote/embedding", use_auth_token="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")
    inference = Inference(model, window="whole")
    embedding = inference(file_path)
    return embedding

# 比較音頻嵌入
def compare_audio_embeddings(embedding1, embedding2):
    similarity = 1 - cosine(embedding1, embedding2)
    return similarity

# 比較文本
def compare_text(text1, text2):
    words1 = text1.split()
    words2 = text2.split()
    return SequenceMatcher(None, words1, words2).ratio(), SequenceMatcher(None, words1, words2).get_opcodes()

# 處理保存音頻並進行比對的路由
@app.route('/save_audio_by_text', methods=['POST'])
def save_audio_by_text():
    try:
        # 獲取上傳的音頻文件和句子内容
        audio_file = request.files['audio_data'].read()
        text_content = request.form.get('text_content')

        if not text_content:
            return jsonify({'success': False, 'message': '句子内容为空，无法保存录音。'}), 400

        # 從資料庫中根據文本獲取句子和原始音頻文件
        conn = cnxpool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, audio_file FROM Sentence WHERE content = %s", (text_content,))
        sentence = cursor.fetchone()

        if not sentence:
            return jsonify({'success': False, 'message': '未找到相应的句子ID。'}), 400

        sentence_id = sentence['id']
        original_audio = sentence['audio_file']

        #獲取用户 email 並確定用户 ID
        user_email = session.get('email')
        if not user_email:
            return jsonify({'success': False, 'message': '用户未登录，无法保存录音。'}), 401

        user_id = get_user_id(user_email)
        recording_date = datetime.datetime.now().date()

        # 檢查是否已有同一天的錄音紀錄
        cursor.execute("""
            SELECT id FROM UserRecordings WHERE user_id = %s AND sentence_id = %s AND recording_date = %s
        """, (user_id, sentence_id, recording_date))
        existing_recording = cursor.fetchone()

        # 確定臨時資料夾路徑
        tmp_dir = '/tmp/audio_files'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        
        user_audio_path = os.path.join(tmp_dir, 'user_audio.wav')
        original_audio_path = os.path.join(tmp_dir, 'original_audio.wav')

        # 保存用户音頻為 wav 文件
        save_audio_as_wav(audio_file, user_audio_path)

        # 保存原始音頻為 wav 文件
        save_audio_as_wav(original_audio, original_audio_path)

        # 提取音頻嵌入並進行比對
        embedding1 = extract_audio_embedding(user_audio_path)
        embedding2 = extract_audio_embedding(original_audio_path)

        similarity_score = compare_audio_embeddings(embedding1, embedding2)

        # 進行語音識別並進行比對
        recognized_text_user = recognize_speech(user_audio_path)
        recognized_text_original = recognize_speech(original_audio_path)

        text_similarity, diff_ops = compare_text(recognized_text_user, recognized_text_original)

        # 定義相似度闊值
        audio_threshold = 0.1
        text_threshold = 0.99

        # 根據相似度结果确定消息
        feedback_message = ""
        if similarity_score < audio_threshold and text_similarity < text_threshold:
            feedback_message = "大錯特錯，給我重念"
        elif similarity_score < audio_threshold and text_similarity > text_threshold:
            feedback_message = "念對了，但發音不標準"
        elif similarity_score > audio_threshold and text_similarity > text_threshold:
            feedback_message = "你好棒，念的很好"

        # 生成文本差異的结果
        result = {
            'success': True,
            'similarity_score': similarity_score,
            'text_similarity': text_similarity,
            'recognized_text_user': recognized_text_user,
            'recognized_text_original': recognized_text_original,
            'feedback_message': feedback_message,
            'diff_ops': []
        }

        if similarity_score > audio_threshold:
            if text_similarity < text_threshold:
                for tag, i1, i2, j1, j2 in diff_ops:
                    if tag != 'equal':
                        result['diff_ops'].append({
                            'text1': ' '.join(recognized_text_user.split()[i1:i2]),
                            'text2': ' '.join(recognized_text_original.split()[j1:j2])
                        })

        # 更新或插入用户錄音紀錄並儲存比對结果
        if existing_recording:
            cursor.execute("""
                UPDATE UserRecordings 
                SET audio_file = %s, similarity_score = %s, text_similarity = %s, diff_ops = %s, 
                    recognized_text_user = %s, recognized_text_original = %s 
                WHERE id = %s
            """, (audio_file, similarity_score, text_similarity, json.dumps(result['diff_ops']), 
                  recognized_text_user, recognized_text_original, existing_recording['id']))
        else:
            cursor.execute("""
                INSERT INTO UserRecordings (user_id, sentence_id, audio_file, recording_date, similarity_score, text_similarity, diff_ops, recognized_text_user, recognized_text_original) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, sentence_id, audio_file, recording_date, similarity_score, text_similarity, 
                  json.dumps(result['diff_ops']), recognized_text_user, recognized_text_original))

        conn.commit()
        cursor.close()
        conn.close()

        # 返回比對结果
        return jsonify(result)

    except Exception as e:
        print(f"Error saving audio: {e}")
        return jsonify({'success': False, 'message': '录音保存失败。'}), 500

@app.route('/learning_progress', methods=['GET'])
def student_learning_progress():
    user_email = session.get('email')

    if not user_email:
        return jsonify({'error': '未登录'}), 401

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 查詢學學過的所有課程
    cursor.execute("""
        SELECT DISTINCT c.id, c.name
        FROM UserRecordings r
        JOIN Sentence s ON r.sentence_id = s.id
        JOIN Course c ON s.course_id = c.id
        JOIN users u ON r.user_id = u.id
        WHERE u.GoogleEmail = %s
    """, (user_email,))
    courses = cursor.fetchall()

    data = {
        'courses': courses,
        'sentences': [],
        'current_course': None,
        'current_sentence': None,
        'dates': [],
        'scores': []
    }

    cursor.close()
    conn.close()

    return render_template('student_learning_progress.html', data=data)

@app.route('/get_student_sentences/<int:course_id>', methods=['GET'])
def get_student_sentences(course_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 查詢課程下的句子
    cursor.execute("""
        SELECT s.id, s.content
        FROM Sentence s
        WHERE s.course_id = %s
    """, (course_id,))
    sentences = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(sentences)


@app.route('/get_student_progress/<int:sentence_id>', methods=['GET'])
def get_student_progress(sentence_id):
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 查詢句子的學習進度
    cursor.execute("""
        SELECT r.recording_date, (r.similarity_score * 0.1 + r.text_similarity * 0.9) * 100 AS score
        FROM UserRecordings r
        JOIN Sentence s ON r.sentence_id = s.id
        WHERE r.sentence_id = %s
        ORDER BY r.recording_date
    """, (sentence_id,))
    progress_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # 返回圖表所需的數據
    return jsonify([{
        'recording_date': row['recording_date'].strftime('%Y-%m-%d'),
        'score': round(row['score'], 2)
    } for row in progress_data])

# 學生學習成果頁面
@app.route('/student_learning_results', methods=['GET'])
def student_learning_results():
    user_email = session.get('email')
    
    if not user_email:
        return jsonify({'error': '未登录'}), 401

    # 獲取資料庫數據
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 獲取學生的學習紀錄，包括識別文本的差異
    query = """
        SELECT r.id, r.recognized_text_user, r.recognized_text_original, r.diff_ops, r.similarity_score, r.text_similarity, r.audio_file, s.content AS sentence_text
        FROM UserRecordings r
        JOIN Sentence s ON r.sentence_id = s.id
        JOIN users u ON r.user_id = u.id
        WHERE u.GoogleEmail = %s
        ORDER BY r.recording_date DESC
    """
    cursor.execute(query, (user_email,))
    learning_records = cursor.fetchall()

    # 處理和解析 `diff_ops`
    results = []
    for record in learning_records:
        try:
            diff_ops = json.loads(record['diff_ops'])
            validated_diff_ops = []
            for op in diff_ops:
                if 'text1' in op and 'text2' in op:
                    validated_diff_ops.append(op)
            record['diff_ops'] = validated_diff_ops
        except Exception as e:
            print(f"Invalid diff_op format: {record['diff_ops']} - {e}")
            record['diff_ops'] = []  # 如果解析失败，设置为空列表
        
        # 將音頻數據轉為 base64
        record['audio_file_base64'] = base64.b64encode(record['audio_file']).decode('utf-8')
        
        # 文本相似度乘以 100 並保留兩位小數
        record['text_similarity'] = round(record['text_similarity'] * 100, 2)

        # 查找第一个錯誤單字並查詢與其匹配的其他句子
        word_links = {}
        first_wrong_word = None
        for op in record['diff_ops']:
            if 'text2' in op and op['text2'] and not first_wrong_word:  # 只取第一个錯誤單字
                first_wrong_word = op['text2']
                # 使用正則表達式匹配句子中包含錯誤單字的句子，并排除原始句子本身
                cursor.execute("""
                    SELECT s.id AS sentence_id, s.content AS sentence_text, c.id AS course_id
                    FROM Sentence s
                    JOIN Course c ON s.course_id = c.id
                    WHERE s.content REGEXP %s AND s.content != %s AND c.is_open = TRUE
                """, (r'\b' + first_wrong_word + r'\b', record['sentence_text']))
                word_sentences = cursor.fetchall()

                if word_sentences:
                    word_links[first_wrong_word] = word_sentences[0]  # 只取第一个匹配的句子
                else:
                    word_links[first_wrong_word] = None

        record['word_links'] = word_links
        results.append(record)

    cursor.close()
    conn.close()

    return render_template('student_learning_results.html', results=results)

# 查找類似單字的句子
@app.route('/search_similar_words', methods=['POST'])
def search_similar_words():
    word = request.form.get('word')

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 使用正則表達式，精確匹配整个單字
    query = """
        SELECT s.id AS sentence_id, s.content AS sentence_text, c.id AS course_id, c.name AS course_name
        FROM Sentence s
        JOIN Course c ON s.course_id = c.id
        WHERE s.content REGEXP %s
    """
    # \b 表示單字邊界，確保是完全匹配
    pattern = r'\\b' + word + r'\\b'
    cursor.execute(query, (pattern,))
    similar_sentences = cursor.fetchall()

    cursor.close()
    conn.close()

    if similar_sentences:
        return jsonify({'success': True, 'sentences': similar_sentences})
    else:
        return jsonify({'success': False, 'message': '无类似的句子'})

# 註冊 Blueprint
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(admin_bp, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=81)
