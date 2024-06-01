import os

# 添加這一行來設置環境變量
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import base64
import datetime
import os
import random
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from oauthlib.oauth2 import WebApplicationClient
import requests
from mysql.connector import pooling

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Google OAuth 2.0 配置
GOOGLE_CLIENT_ID = '75296281877-dpk0mit858rlc46edltua30od70kpsac.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'  # 替換為您的Google客戶端密鑰
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# 創建資料庫連接池
db_config = {
    'user': 'case113201',
    'password': '@Ntub_113201',
    'host': '140.131.114.242',
    'database': '113-NTUB',
    'pool_name': 'mypool',
    'pool_size': 5
}
cnxpool = pooling.MySQLConnectionPool(**db_config)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# 獲取 Google 提供的配置信息
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('main'))
    return render_template('index.html')

@app.route('/login')
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + '/callback',
        scope=['openid', 'email', 'profile'],
    )
    return redirect(request_uri)

@app.route('/login/callback')
def callback():
    code = request.args.get('code')
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg['token_endpoint']

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(token_response.text)

    userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get('email_verified'):
        unique_id = userinfo_response.json()['sub']
        users_email = userinfo_response.json()['email']
        users_name = userinfo_response.json()['name']
        picture = userinfo_response.json()['picture']

        session['email'] = users_email
        session['name'] = users_name

        conn = cnxpool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE GoogleEmail = %s", (users_email,))
        user = cursor.fetchone()

        if user is None:
            cursor.execute("""
                INSERT INTO users (userName, GoogleEmail, icon) 
                VALUES (%s, %s, %s)
            """, (users_name, users_email, picture))
            conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('main'))
    else:
        return "用戶身份驗證失敗", 400

@app.route('/main')
def main():
    if 'email' not in session:
        return redirect(url_for('index'))

    user_email = session['email']
    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT userName FROM users WHERE GoogleEmail = %s", (user_email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

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

# 保存錄音
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

    # 更新或插入錄音記錄到 vocabularyUserVoice 表
    cursor.execute("""
        INSERT INTO vocabularyUserVoice (user_voice, STT, date, vocabulary_id, user_id)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE user_voice = VALUES(user_voice), STT = VALUES(STT)
    """, (base64.b64decode(user_voice), stt, date_now, vocabulary_id, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

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
    for topic in topics:
        topic['icon'] = base64.b64encode(topic['icon']).decode('utf-8')
    cursor.close()
    conn.close()
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
    
    vocabulary['vocabulary_voice'] = base64.b64encode(vocabulary['vocabulary_voice']).decode('utf-8')
    cursor.close()
    conn.close()
    return render_template('vocabulary_detail.html', vocabulary=vocabulary, is_collected=is_collected)

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

##對話主題
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
    
    # 对于每个主题，获取其难度等级
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

# 保存錄音
@app.route('/save_recording', methods=['POST'])
def save_recording():
    data = request.form
    user_voice = data['user_voice']
    stt = data['stt']
    vocabulary_id = data.get('vocabulary_id')  # 單字錄音
    conversation_id = data.get('conversation_id')  # 對話錄音
    user_email = session['email']
    date_now = datetime.datetime.now().date()

    conn = cnxpool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 獲取用戶ID
    user_id = get_user_id(user_email)

    if vocabulary_id:
        # 更新或插入錄音記錄到 vocabularyUserVoice 表
        cursor.execute("""
            INSERT INTO vocabularyUserVoice (user_voice, STT, date, vocabulary_id, user_id)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE user_voice = VALUES(user_voice), STT = VALUES(STT)
        """, (base64.b64decode(user_voice), stt, date_now, vocabulary_id, user_id))
    elif conversation_id:
        # 更新或插入錄音記錄到 conversationUserVoice 表
        cursor.execute("""
            INSERT INTO conversationUserVoice (user_voice, STT, date, conversation_id, user_id)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE user_voice = VALUES(user_voice), STT = VALUES(STT)
        """, (base64.b64decode(user_voice), stt, date_now, conversation_id, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success"})

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
            SELECT v.vocabulary_en, v.vocabulary_tw, v.part_of_speech, v.ipa, v.example, v.class, vuv.user_voice, vuv.STT, vuv.date
            FROM vocabularyUserVoice vuv
            JOIN vocabulary v ON vuv.vocabulary_id = v.id
            WHERE vuv.user_id = %s AND vuv.date = %s
            ORDER BY vuv.date ASC
        """, (user_id, date_filter))
    else:
        cursor.execute("""
            SELECT v.vocabulary_en, v.vocabulary_tw, v.part_of_speech, v.ipa, v.example, v.class, vuv.user_voice, vuv.STT, vuv.date
            FROM vocabularyUserVoice vuv
            JOIN vocabulary v ON vuv.vocabulary_id = v.id
            WHERE vuv.user_id = %s
            ORDER BY vuv.date ASC
        """, (user_id,))
    
    learning_history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for record in learning_history:
        record['user_voice'] = base64.b64encode(record['user_voice']).decode('utf-8')
    
    return render_template('learning_history_vocabulary.html', learning_history=learning_history, date_filter=date_filter)

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
            SELECT c.conversation_en, c.conversation_tw, cuv.user_voice, cuv.STT, cuv.date
            FROM conversationUserVoice cuv
            JOIN conversation c ON cuv.conversation_id = c.id
            WHERE cuv.user_id = %s AND cuv.date = %s
            ORDER BY cuv.date ASC
        """, (user_id, date_filter))
    else:
        cursor.execute("""
            SELECT c.conversation_en, c.conversation_tw, cuv.user_voice, cuv.STT, cuv.date
            FROM conversationUserVoice cuv
            JOIN conversation c ON cuv.conversation_id = c.id
            WHERE cuv.user_id = %s
            ORDER BY cuv.date ASC
        """, (user_id,))
    
    learning_history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    for record in learning_history:
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
            ch.character_name, i.icon
        FROM conversationCollect cc
        JOIN conversation c ON cc.conversation_id = c.id
        JOIN characters ch ON c.character_id = ch.id
        JOIN icon i ON ch.icon_id = i.id
        WHERE cc.user_id = %s
        ORDER BY c.id ASC
    """, (user_id,))
    
    conversations = cursor.fetchall()
    
    for conversation in conversations:
        conversation['icon'] = base64.b64encode(conversation['icon']).decode('utf-8')
        conversation['conversation_voice'] = base64.b64encode(conversation['conversation_voice']).decode('utf-8')
    
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
            v.example, v.vocabulary_voice, vt.name as topic_name
        FROM vocabularyCollect vc
        JOIN vocabulary v ON vc.vocabulary_id = v.id
        JOIN vocabularyTopic vt ON v.topic_id = vt.id
        WHERE vc.user_id = %s
        ORDER BY v.id ASC
    """, (user_id,))
    
    vocabularies = cursor.fetchall()
    
    for vocabulary in vocabularies:
        vocabulary['vocabulary_voice'] = base64.b64encode(vocabulary['vocabulary_voice']).decode('utf-8')
    
    cursor.close()
    conn.close()
    
    return render_template('learning_notes_vocabulary.html', vocabularies=vocabularies)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)