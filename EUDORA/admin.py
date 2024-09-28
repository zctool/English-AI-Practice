from flask import Blueprint, jsonify, render_template, request, redirect, send_file, url_for, flash, g, session
import mysql.connector.pooling as pooling
from functools import wraps
import mysql.connector
import base64
import io
import os
import secrets

admin_bp = Blueprint('admin', __name__)

# 使用环境变量或生成随机密钥
admin_bp.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

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

# 檢查文件類型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

# 獲取資料庫連接
def get_db_connection():
    return cnxpool.get_connection()

# 關閉資料庫連接
def close_db_connection(cursor, connection):
    if cursor:
        cursor.close()
    if connection:
        connection.close()

# 管理員身份驗證
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('email') or session['email'] != 'eudora113201@gmail.com':
            flash('You do not have access to this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 登出
@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 管理首頁
@admin_bp.route('/')
@admin_required
def admin_index():
    return render_template('admin_index.html')


# 管理教學內容
@admin_bp.route('/admin_index')
@admin_required
def admin_home():
    return render_template('admin_index.html')

# 新增單詞主題
@admin_bp.route('/add_vocabulary_topic', methods=['GET', 'POST'])
@admin_required
def add_vocabulary_topic():
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = "INSERT INTO vocabularyTopic (name) VALUES (%s)"
            cursor.execute(query, (name,))
            topic_id = cursor.lastrowid

            if icon_file and allowed_file(icon_file.filename):
                icon_data = icon_file.read()
                cursor.execute("INSERT INTO vocabularyTopicIcon (topic_id, icon) VALUES (%s, %s)", (topic_id, icon_data))

            connection.commit()
            flash('Vocabulary Topic added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)

        return redirect(url_for('admin.add_vocabulary_topic'))
    return render_template('add_vocabularyTopic.html')

# 新增單字內容
@admin_bp.route('/add_vocabulary', methods=['GET', 'POST'])
@admin_required
def add_vocabulary():
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        vocabulary_en = request.form['vocabulary_en']
        vocabulary_tw = request.form['vocabulary_tw']
        part_of_speech = request.form['part_of_speech']
        ipa = request.form['ipa']
        example = request.form['example']
        difficulty_class = request.form['class']
        vocabulary_voice = request.files['vocabulary_voice']

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            voice_data = vocabulary_voice.read()
            query = """
                INSERT INTO vocabulary (topic_id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, vocabulary_voice, class)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (topic_id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, voice_data, difficulty_class))
            connection.commit()
            flash('Vocabulary added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)

        return redirect(url_for('admin.add_vocabulary'))
    else:
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM vocabularyTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topics = []
        finally:
            close_db_connection(cursor, connection)
        return render_template('add_vocabulary.html', topics=topics)

# 獲取指定主題的難易度
@admin_bp.route('/get_vocabulary_difficulty_classes/<int:topic_id>', methods=['GET'])
@admin_required
def get_vocabulary_difficulty_classes(topic_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT class FROM conversationSituation WHERE topic_id = %s", (topic_id,))
        difficulty_classes = cursor.fetchall()
        return jsonify([{'class': class_item[0]} for class_item in difficulty_classes])
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        close_db_connection(cursor, connection)

# 獲取指定難易度和主題的情境
@admin_bp.route('/get_vocabulary_situations/<int:topic_id>/<string:difficulty_class>', methods=['GET'])
@admin_required
def get_vocabulary_situations(topic_id, difficulty_class):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT id, situation FROM conversationSituation WHERE topic_id = %s AND class = %s"
        cursor.execute(query, (topic_id, difficulty_class))
        situations = cursor.fetchall()
        return jsonify([{'id': situation[0], 'situation': situation[1]} for situation in situations])
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        close_db_connection(cursor, connection)

# 獲取指定情境的人物
@admin_bp.route('/get_vocabulary_characters_by_situation/<int:situation_id>', methods=['GET'])
@admin_required
def get_vocabulary_characters_by_situation(situation_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT id, character_name FROM characters WHERE situation_id = %s"
        cursor.execute(query, (situation_id,))
        characters = cursor.fetchall()
        return jsonify([{'id': character[0], 'character_name': character[1]} for character in characters])
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        close_db_connection(cursor, connection)

# 查看和编辑單字主題
@admin_bp.route('/admin_vocabulary_topics')
@admin_required
def admin_vocabulary_topics():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM vocabularyTopic")
        topics = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        topics = []
    finally:
        close_db_connection(cursor, connection)
    return render_template('admin_vocabulary_topics.html', topics=topics)

# 编辑單字主題
@admin_bp.route('/edit_vocabulary_topic/<int:topic_id>', methods=['GET', 'POST'])
@admin_required
def edit_vocabulary_topic(topic_id):
    connection = None
    cursor = None
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = "UPDATE vocabularyTopic SET name = %s WHERE id = %s"
            cursor.execute(query, (name, topic_id))

            if icon_file and allowed_file(icon_file.filename):
                icon_data = icon_file.read()
                cursor.execute("REPLACE INTO vocabularyTopicIcon (topic_id, icon) VALUES (%s, %s)", (topic_id, icon_data))

            connection.commit()
            flash('Vocabulary Topic updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.admin_vocabulary_topics'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM vocabularyTopic WHERE id = %s", (topic_id,))
            topic = cursor.fetchone()

            cursor.execute("SELECT icon FROM vocabularyTopicIcon WHERE topic_id = %s", (topic_id,))
            icon = cursor.fetchone()

        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topic = None
            icon = None
        finally:
            close_db_connection(cursor, connection)
        return render_template('edit_vocabulary_topic.html', topic=topic, icon=icon, topic_id=topic_id)

# 删除單字主題
@admin_bp.route('/delete_vocabulary_topic/<int:topic_id>')
@admin_required
def delete_vocabulary_topic(topic_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # 删除相关的图标
        cursor.execute("DELETE FROM vocabularyTopicIcon WHERE topic_id = %s", (topic_id,))

        # 删除主題
        cursor.execute("DELETE FROM vocabularyTopic WHERE id = %s", (topic_id,))

        connection.commit()
        flash('Vocabulary Topic deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)
    return redirect(url_for('admin.admin_vocabulary_topics'))

# 查看和编辑單字
@admin_bp.route('/vocabularies')
@admin_required
def vocabularies():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, vocabulary_en, vocabulary_tw FROM vocabulary")
        vocabularies = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        vocabularies = []
    finally:
        close_db_connection(cursor, connection)
    return render_template('vocabularies.html', vocabularies=vocabularies)

# 编辑單字
@admin_bp.route('/edit_vocabulary/<int:vocabulary_id>', methods=['GET', 'POST'])
@admin_required
def edit_vocabulary(vocabulary_id):
    connection = None
    cursor = None
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        vocabulary_en = request.form['vocabulary_en']
        vocabulary_tw = request.form['vocabulary_tw']
        part_of_speech = request.form['part_of_speech']
        ipa = request.form['ipa']
        example = request.form['example']
        difficulty_class = request.form['class']
        vocabulary_voice = request.files.get('vocabulary_voice')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            if vocabulary_voice:
                voice_data = vocabulary_voice.read()
                query = """
                    UPDATE vocabulary SET topic_id = %s, vocabulary_en = %s, vocabulary_tw = %s, part_of_speech = %s, ipa = %s, example = %s, vocabulary_voice = %s, class = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, voice_data, difficulty_class, vocabulary_id))
            else:
                query = """
                    UPDATE vocabulary SET topic_id = %s, vocabulary_en = %s, vocabulary_tw = %s, part_of_speech = %s, ipa = %s, example = %s, class = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, difficulty_class, vocabulary_id))
            connection.commit()
            flash('Vocabulary updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.vocabularies'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, topic_id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, class FROM vocabulary WHERE id = %s", (vocabulary_id,))
            vocabulary = cursor.fetchone()
            cursor.execute("SELECT id, name FROM vocabularyTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            vocabulary = None
            topics = []
        finally:
            close_db_connection(cursor, connection)
        return render_template('edit_vocabulary.html', vocabulary=vocabulary, topics=topics)

# 删除單字
@admin_bp.route('/delete_vocabulary/<int:vocabulary_id>')
@admin_required
def delete_vocabulary(vocabulary_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM vocabulary WHERE id = %s", (vocabulary_id,))
        connection.commit()
        flash('Vocabulary deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)
    return redirect(url_for('admin.vocabularies'))

# 新增對話主題
@admin_bp.route('/add_conversation_topic', methods=['GET', 'POST'])
@admin_required
def add_conversation_topic():
    connection = None
    cursor = None
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            check_query = "SELECT COUNT(*) FROM conversationTopic WHERE name = %s"
            cursor.execute(check_query, (name,))
            result = cursor.fetchone()

            if result[0] > 0:
                flash('Topic with the same name already exists!', 'danger')
            else:
                query = "INSERT INTO conversationTopic (name) VALUES (%s)"
                cursor.execute(query, (name,))
                topic_id = cursor.lastrowid

                if icon_file and allowed_file(icon_file.filename):
                    icon_data = icon_file.read()
                    cursor.execute("INSERT INTO conversationTopicIcon (topic_id, icon) VALUES (%s, %s)", (topic_id, icon_data))

                connection.commit()
                flash('Conversation Topic added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.add_conversation_topic'))
    return render_template('add_conversationTopic.html')

# 新增對話情境
@admin_bp.route('/add_conversation_situation', methods=['GET', 'POST'])
@admin_required
def add_conversation_situation():
    connection = None
    cursor = None
    if request.method == 'POST':
        situation = request.form['situation']
        topic_id = request.form['topic_id']
        difficulty_class = request.form['class']

        character_names = request.form.getlist('character_name')
        icons = request.files.getlist('character_icon')

        if not character_names or not icons:
            flash('至少需要添加一個角色才能提交表單。', 'danger')
            return redirect(url_for('admin.add_conversation_situation'))

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = "INSERT INTO conversationSituation (situation, topic_id, class) VALUES (%s, %s, %s)"
            cursor.execute(query, (situation, topic_id, difficulty_class))
            situation_id = cursor.lastrowid

            for i in range(len(character_names)):
                character_name = character_names[i]
                character_icon_file = icons[i]

                if character_icon_file and allowed_file(character_icon_file.filename):
                    character_icon_data = character_icon_file.read()
                    cursor.execute("INSERT INTO icon (icon) VALUES (%s)", (character_icon_data,))
                    icon_id = cursor.lastrowid
                    cursor.execute("INSERT INTO characters (character_name, icon_id, situation_id) VALUES (%s, %s, %s)", (character_name, icon_id, situation_id))

            connection.commit()
            flash('Conversation Situation added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.add_conversation_situation'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM conversationTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topics = []
        finally:
            close_db_connection(cursor, connection)
        return render_template('add_conversation_situation.html', topics=topics)

# 新增對話內容
@admin_bp.route('/add_conversation', methods=['GET', 'POST'])
@admin_required
def add_conversation():
    connection = None
    cursor = None
    if request.method == 'POST':
        situation_id = request.form['situation_id']
        character_id = request.form['character_id']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        conversation_voice = request.files['conversation_voice']

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            # 从 conversationSituation 表中查询 class 字段
            cursor.execute("SELECT class FROM conversationSituation WHERE id = %s", (situation_id,))
            situation = cursor.fetchone()
            if situation is None:
                flash('Invalid situation ID.', 'danger')
                return redirect(url_for('admin_bp.add_conversation'))

            voice_data = conversation_voice.read() if conversation_voice else None
            query = """
                INSERT INTO conversation (situation_id, character_id, conversation_en, conversation_tw, conversation_voice)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (situation_id, character_id, conversation_en, conversation_tw, voice_data))
            connection.commit()
            flash('Conversation added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.add_conversation'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM conversationTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topics = []
        finally:
            close_db_connection(cursor, connection)
        return render_template('add_conversation.html', topics=topics)

# 查看和编辑对话主题
@admin_bp.route('/admin_conversation_topics')
@admin_required
def admin_conversation_topics():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM conversationTopic")
        topics = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        topics = []
    finally:
        close_db_connection(cursor, connection)
    return render_template('admin_conversation_topics.html', topics=topics)

# 编辑对话主题
@admin_bp.route('/edit_conversation_topic/<int:topic_id>', methods=['GET', 'POST'])
@admin_required
def edit_conversation_topic(topic_id):
    connection = None
    cursor = None
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = "UPDATE conversationTopic SET name = %s WHERE id = %s"
            cursor.execute(query, (name, topic_id))

            if icon_file and allowed_file(icon_file.filename):
                icon_data = icon_file.read()
                cursor.execute("REPLACE INTO conversationTopicIcon (topic_id, icon) VALUES (%s, %s)", (topic_id, icon_data))

            connection.commit()
            flash('Conversation Topic updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.admin_conversation_topics'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM conversationTopic WHERE id = %s", (topic_id,))
            topic = cursor.fetchone()

            cursor.execute("SELECT icon FROM conversationTopicIcon WHERE topic_id = %s", (topic_id,))
            icon = cursor.fetchone()

        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topic = None
            icon = None
        finally:
            close_db_connection(cursor, connection)
        return render_template('edit_conversation_topic.html', topic=topic, icon=icon, topic_id=topic_id)

# 删除对话主题
@admin_bp.route('/delete_conversation_topic/<int:topic_id>')
@admin_required
def delete_conversation_topic(topic_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # 刪除引用這些主題的外鍵
        cursor.execute("DELETE FROM conversationSituation WHERE topic_id = %s", (topic_id,))

        # 刪除相關的圖標
        cursor.execute("DELETE FROM conversationTopicIcon WHERE topic_id = %s", (topic_id,))

        # 刪除主題
        cursor.execute("DELETE FROM conversationTopic WHERE id = %s", (topic_id,))

        connection.commit()
        flash('Conversation Topic deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)
    return redirect(url_for('admin.admin_conversation_topics'))

# 查看和编辑对话
@admin_bp.route('/conversations')
@admin_required
def conversations():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
            SELECT c.id, c.conversation_en, c.conversation_tw, cs.situation, cs.class, ct.name AS topic_name
            FROM conversation c
            JOIN conversationSituation cs ON c.situation_id = cs.id
            JOIN conversationTopic ct ON cs.topic_id = ct.id
        """
        cursor.execute(query)
        conversations = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        conversations = []
    finally:
        close_db_connection(cursor, connection)
    return render_template('conversations.html', conversations=conversations)

# 编辑对话
@admin_bp.route('/edit_conversation/<int:conversation_id>', methods=['GET', 'POST'])
@admin_required
def edit_conversation(conversation_id):
    connection = None
    cursor = None
    if request.method == 'POST':
        situation_id = request.form['situation_id']
        character_id = request.form['character_id']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        conversation_voice = request.files.get('conversation_voice')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            if conversation_voice:
                voice_data = conversation_voice.read()
                query = """
                    UPDATE conversation SET situation_id = %s, character_id = %s, conversation_en = %s, conversation_tw = %s, conversation_voice = %s
                    WHERE id = %s
                """
                cursor.execute(query, (situation_id, character_id, conversation_en, conversation_tw, voice_data, conversation_id))
            else:
                query = """
                    UPDATE conversation SET situation_id = %s, character_id = %s, conversation_en = %s, conversation_tw = %s
                    WHERE id = %s
                """
                cursor.execute(query, (situation_id, character_id, conversation_en, conversation_tw, conversation_id))
            connection.commit()
            flash('Conversation updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.conversations'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT c.id, c.conversation_en, c.conversation_tw, c.character_id, cs.id AS situation_id, cs.situation, ct.id AS topic_id, ct.name AS topic_name, cs.class
                FROM conversation c
                JOIN conversationSituation cs ON c.situation_id = cs.id
                JOIN conversationTopic ct ON cs.topic_id = ct.id
                WHERE c.id = %s
            """, (conversation_id,))
            conversation = cursor.fetchone()
            cursor.execute("SELECT id, situation FROM conversationSituation")
            situations = cursor.fetchall()
            cursor.execute("SELECT id, character_name FROM characters WHERE situation_id = %s", (conversation[4],))
            characters = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            conversation = None
            situations = []
            characters = []
        finally:
            close_db_connection(cursor, connection)
        return render_template('edit_conversation.html', conversation=conversation, situations=situations, characters=characters)

# 删除对话
@admin_bp.route('/delete_conversation/<int:conversation_id>')
@admin_required
def delete_conversation(conversation_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM conversation WHERE id = %s", (conversation_id,))
        connection.commit()
        flash('Conversation deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)
    return redirect(url_for('admin.conversations'))

# 查看和编辑对话情境
@admin_bp.route('/admin_conversation_situations')
@admin_required
def admin_conversation_situations():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT cs.id, cs.situation, cs.class, ct.name AS topic_name
            FROM conversationSituation cs
            JOIN conversationTopic ct ON cs.topic_id = ct.id
        """)
        situations = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        situations = []
    finally:
        close_db_connection(cursor, connection)
    return render_template('admin_conversation_situations.html', situations=situations)

# 编辑对话情境
@admin_bp.route('/edit_conversation_situation/<int:situation_id>', methods=['GET', 'POST'])
@admin_required
def edit_conversation_situation(situation_id):
    connection = None
    cursor = None
    if request.method == 'POST':
        situation = request.form['situation']
        topic_id = request.form['topic_id']

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = "UPDATE conversationSituation SET situation = %s, topic_id = %s WHERE id = %s"
            cursor.execute(query, (situation, topic_id, situation_id))

            connection.commit()
            flash('Conversation Situation updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.admin_conversation_situations'))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT situation, topic_id FROM conversationSituation WHERE id = %s", (situation_id,))
            situation = cursor.fetchone()

            cursor.execute("SELECT id, name FROM conversationTopic")
            topics = cursor.fetchall()

        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            situation = None
            topics = []
        finally:
            close_db_connection(cursor, connection)
        return render_template('edit_conversation_situation.html', situation=situation, topics=topics, situation_id=situation_id)

# 删除对话情境
@admin_bp.route('/delete_conversation_situation/<int:situation_id>')
@admin_required
def delete_conversation_situation(situation_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        # 删除相关的角色
        cursor.execute("DELETE FROM characters WHERE situation_id = %s", (situation_id,))
        # 删除情境
        cursor.execute("DELETE FROM conversationSituation WHERE id = %s", (situation_id,))
        connection.commit()
        flash('Conversation Situation deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)
    return redirect(url_for('admin.admin_conversation_situations'))

# 查看和编辑人物
@admin_bp.route('/characters/<int:situation_id>')
@admin_required
def characters(situation_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, character_name FROM characters WHERE situation_id = %s", (situation_id,))
        characters = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        characters = []
    finally:
        close_db_connection(cursor, connection)
    return render_template('characters.html', characters=characters, situation_id=situation_id)

# 编辑人物
@admin_bp.route('/edit_character/<int:character_id>', methods=['GET', 'POST'])
@admin_required
def edit_character(character_id):
    connection = None
    cursor = None
    if request.method == 'POST':
        character_name = request.form['character_name']
        icon_file = request.files.get('icon')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            if icon_file and allowed_file(icon_file.filename):
                icon_data = icon_file.read()
                cursor.execute("INSERT INTO icon (icon) VALUES (%s)", (icon_data,))
                icon_id = cursor.lastrowid
                query = "UPDATE characters SET character_name = %s, icon_id = %s WHERE id = %s"
                cursor.execute(query, (character_name, icon_id, character_id))
            else:
                query = "UPDATE characters SET character_name = %s WHERE id = %s"
                cursor.execute(query, (character_name, character_id))
            connection.commit()
            flash('Character updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            close_db_connection(cursor, connection)
        return redirect(url_for('admin.characters', situation_id=request.form['situation_id']))
    else:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, character_name FROM characters WHERE id = %s", (character_id,))
            character = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            character = None
        finally:
            close_db_connection(cursor, connection)
        return render_template('edit_character.html', character=character, situation_id=request.args.get('situation_id'))

# 删除人物
@admin_bp.route('/delete_character/<int:character_id>/<int:situation_id>')
@admin_required
def delete_character(character_id, situation_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM characters WHERE id = %s", (character_id,))
        connection.commit()
        flash('Character deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)
    return redirect(url_for('admin.characters', situation_id=situation_id))

# 獲取圖標
@admin_bp.route('/icon/<int:situation_id>')
@admin_required
def icon(situation_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT icon FROM conversationTopicIcon WHERE topic_id = %s", (situation_id,))
        icon = cursor.fetchone()
        if icon and icon[0]:
            return send_file(io.BytesIO(icon[0]), mimetype='image/png')
        else:
            flash('Icon not found', 'danger')
            return '', 404
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return '', 500
    finally:
        close_db_connection(cursor, connection)

# 管理员权限页面
@admin_bp.route('/admin_permission', methods=['GET', 'POST'])
@admin_required
def admin_permission():
    if 'email' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))

    search_query = request.form.get('search', '')

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if search_query:
            cursor.execute("""
                SELECT id, userName, GoogleEmail, role, icon FROM users 
                WHERE userName LIKE %s OR GoogleEmail LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cursor.execute("SELECT id, userName, GoogleEmail, role, icon FROM users")

        users = cursor.fetchall()
        for user in users:
            if user['icon']:
                user['icon'] = base64.b64encode(user['icon']).decode('utf-8')

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        users = []
    finally:
        close_db_connection(cursor, connection)

    return render_template('admin_permission.html', users=users, name=session['name'], search_query=search_query)

# 更新用户角色
@admin_bp.route('/update_user_role', methods=['POST'])
@admin_required
def update_user_role():
    user_id = request.form['user_id']
    new_role = request.form['role']

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
        connection.commit()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        close_db_connection(cursor, connection)

    return redirect(url_for('admin.admin_permission'))

# 删除用户
@admin_bp.route('/delete_user', methods=['POST'])
@admin_required
def delete_user():
    user_id = request.form['user_id']

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # 手動刪除與該使用者相關的資料
        cursor.execute("DELETE FROM vocabularyCollect WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM vocabularyUserVoice WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM conversationCollect WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM conversationUserVoice WHERE user_id = %s", (user_id,))

        # 刪除使用者本身
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

        connection.commit()
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        flash(f"Error: {err}", 'danger')
    finally:
        close_db_connection(cursor, connection)

    return redirect(url_for('admin.admin_permission'))
