import io
from flask import Flask, jsonify, render_template, request, redirect, send_file, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL 数据库连接配置
config = {
    'user': 'case113201',
    'password': '@Ntub_113201',
    'host': '140.131.114.242',
    'database': '113-NTUB',
}

@app.route('/')
def index():
    return render_template('index.html')

# 新增單詞主題
@app.route('/add_vocabulary_topic', methods=['GET', 'POST'])
def add_vocabulary_topic():
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('add_vocabulary_topic'))
    return render_template('add_vocabularyTopic.html')

# 新增單字內容
@app.route('/add_vocabulary', methods=['GET', 'POST'])
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

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('add_vocabulary'))
    else:
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM vocabularyTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topics = []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('add_vocabulary.html', topics=topics)

# 查看和编辑單字主題
@app.route('/vocabulary_topics')
def vocabulary_topics():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM vocabularyTopic")
        topics = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        topics = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('vocabulary_topics.html', topics=topics)

# 编辑單字主題
@app.route('/edit_vocabulary_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_vocabulary_topic(topic_id):
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('vocabulary_topics'))
    else:
        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_vocabulary_topic.html', topic=topic, icon=icon, topic_id=topic_id)

# 删除單字主題
@app.route('/delete_vocabulary_topic/<int:topic_id>')
def delete_vocabulary_topic(topic_id):
    try:
        connection = mysql.connector.connect(**config)
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return redirect(url_for('vocabulary_topics'))

# 查看和编辑單字
@app.route('/vocabularies')
def vocabularies():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, vocabulary_en, vocabulary_tw FROM vocabulary")
        vocabularies = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        vocabularies = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('vocabularies.html', vocabularies=vocabularies)

# 编辑單字
@app.route('/edit_vocabulary/<int:vocabulary_id>', methods=['GET', 'POST'])
def edit_vocabulary(vocabulary_id):
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
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('vocabularies'))
    else:
        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_vocabulary.html', vocabulary=vocabulary, topics=topics)

# 删除單字
@app.route('/delete_vocabulary/<int:vocabulary_id>')
def delete_vocabulary(vocabulary_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM vocabulary WHERE id = %s", (vocabulary_id,))
        connection.commit()
        flash('Vocabulary deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return redirect(url_for('vocabularies'))


# 新增對話主題
@app.route('/add_conversation_topic', methods=['GET', 'POST'])
def add_conversation_topic():
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('add_conversation_topic'))
    return render_template('add_conversationTopic.html')

# 新增對話情境
@app.route('/add_conversation_situation', methods=['GET', 'POST'])
def add_conversation_situation():
    if request.method == 'POST':
        situation = request.form['situation']
        topic_id = request.form['topic_id']
        difficulty_class = request.form['class']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()

            query = "INSERT INTO conversationSituation (situation, topic_id, class) VALUES (%s, %s, %s)"
            cursor.execute(query, (situation, topic_id, difficulty_class))
            situation_id = cursor.lastrowid

            character_names = request.form.getlist('character_name')
            icons = request.files.getlist('character_icon')

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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('add_conversation_situation'))
    else:
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM conversationTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topics = []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('add_conversation_situation.html', topics=topics)

# 新增對話內容
@app.route('/add_conversation', methods=['GET', 'POST'])
def add_conversation():
    if request.method == 'POST':
        situation_id = request.form['situation_id']
        character_id = request.form['character_id']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        difficulty_class = request.form['class']
        conversation_voice = request.files['conversation_voice']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()

            voice_data = conversation_voice.read() if conversation_voice else None
            query = """
                INSERT INTO conversation (situation_id, character_id, conversation_en, conversation_tw, class, conversation_voice)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (situation_id, character_id, conversation_en, conversation_tw, difficulty_class, voice_data))
            connection.commit()
            flash('Conversation added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            if connection:
                connection.rollback()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('add_conversation'))
    else:
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM conversationTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topics = []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('add_conversation.html', topics=topics)

@app.route('/get_difficulty_classes/<int:topic_id>', methods=['GET'])
def get_difficulty_classes(topic_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        query = "SELECT DISTINCT class FROM conversationSituation WHERE topic_id = %s"
        cursor.execute(query, (topic_id,))
        difficulty_classes = cursor.fetchall()
        return jsonify([{'class': class_item[0]} for class_item in difficulty_classes])
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/get_situations/<int:topic_id>/<string:difficulty_class>', methods=['GET'])
def get_situations(topic_id, difficulty_class):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        query = "SELECT id, situation FROM conversationSituation WHERE topic_id = %s AND class = %s"
        cursor.execute(query, (topic_id, difficulty_class))
        situations = cursor.fetchall()
        return jsonify([{'id': situation[0], 'situation': situation[1]} for situation in situations])
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/get_characters_by_situation/<int:situation_id>', methods=['GET'])
def get_characters_by_situation(situation_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        query = "SELECT id, character_name FROM characters WHERE situation_id = %s"
        cursor.execute(query, (situation_id,))
        characters = cursor.fetchall()
        return jsonify([{'id': character[0], 'character_name': character[1]} for character in characters])
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 查看和編輯對話主題
@app.route('/conversation_topics')
def conversation_topics():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM conversationTopic")
        topics = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        topics = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('conversation_topics.html', topics=topics)

#編輯對話主題
@app.route('/edit_conversation_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_conversation_topic(topic_id):
    if request.method == 'POST':
        name = request.form['name']
        icon_file = request.files.get('icon')

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('conversation_topics'))
    else:
        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_conversation_topic.html', topic=topic, icon=icon, topic_id=topic_id)

# 刪除對話主題
@app.route('/delete_conversation_topic/<int:topic_id>')
def delete_conversation_topic(topic_id):
    try:
        connection = mysql.connector.connect(**config)
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return redirect(url_for('conversation_topics'))

# 查看和編輯對話
@app.route('/conversations')
def conversations():
    try:
        connection = mysql.connector.connect(**config)
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('conversations.html', conversations=conversations)

# 編輯對話
@app.route('/edit_conversation/<int:conversation_id>', methods=['GET', 'POST'])
def edit_conversation(conversation_id):
    if request.method == 'POST':
        situation_id = request.form['situation_id']
        character_id = request.form['character_id']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        conversation_voice = request.files.get('conversation_voice')

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('conversations'))
    else:
        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_conversation.html', conversation=conversation, situations=situations, characters=characters)

# 刪除對話
@app.route('/delete_conversation/<int:conversation_id>')
def delete_conversation(conversation_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM conversation WHERE id = %s", (conversation_id,))
        connection.commit()
        flash('Conversation deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return redirect(url_for('conversations'))


# 查看和編輯對話情境
@app.route('/conversation_situations')
def conversation_situations():
    try:
        connection = mysql.connector.connect(**config)
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('conversation_situations.html', situations=situations)

# 編輯對話情境
@app.route('/edit_conversation_situation/<int:situation_id>', methods=['GET', 'POST'])
def edit_conversation_situation(situation_id):
    if request.method == 'POST':
        situation = request.form['situation']
        topic_id = request.form['topic_id']

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('conversation_situations'))
    else:
        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_conversation_situation.html', situation=situation, topics=topics, situation_id=situation_id)

# 刪除對話情境
@app.route('/delete_conversation_situation/<int:situation_id>')
def delete_conversation_situation(situation_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        # 刪除相關的角色
        cursor.execute("DELETE FROM characters WHERE situation_id = %s", (situation_id,))
        # 刪除情境
        cursor.execute("DELETE FROM conversationSituation WHERE id = %s", (situation_id,))
        connection.commit()
        flash('Conversation Situation deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return redirect(url_for('conversation_situations'))

# 查看和编辑人物
@app.route('/characters/<int:situation_id>')
def characters(situation_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, character_name FROM characters WHERE situation_id = %s", (situation_id,))
        characters = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        characters = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('characters.html', characters=characters, situation_id=situation_id)

# 编辑人物
@app.route('/edit_character/<int:character_id>', methods=['GET', 'POST'])
def edit_character(character_id):
    if request.method == 'POST':
        character_name = request.form['character_name']
        icon_file = request.files.get('icon')

        try:
            connection = mysql.connector.connect(**config)
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
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return redirect(url_for('characters', situation_id=request.form['situation_id']))
    else:
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT id, character_name FROM characters WHERE id = %s", (character_id,))
            character = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            character = None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_character.html', character=character, situation_id=request.args.get('situation_id'))

# 删除人物
@app.route('/delete_character/<int:character_id>/<int:situation_id>')
def delete_character(character_id, situation_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM characters WHERE id = %s", (character_id,))
        connection.commit()
        flash('Character deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return redirect(url_for('characters', situation_id=situation_id))

@app.route('/icon/<int:situation_id>')
def icon(situation_id):
    try:
        connection = mysql.connector.connect(**config)
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 檢查文件類型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)
