from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
import datetime
import os

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

# 新增單字主題
@app.route('/add_vocabulary_topic', methods=['GET', 'POST'])
def add_vocabulary_topic():
    if request.method == 'POST':
        name = request.form['name']
        difficulty_class = request.form['class']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "INSERT INTO vocabularyTopic (name, class) VALUES (%s, %s)"
            cursor.execute(query, (name, difficulty_class))
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
        part_of_speech = request.form['PartOfSpeech']
        ipa = request.form['IPA']
        example = request.form['example']
        difficulty_class = request.form['class']
        vocabulary_voice = request.files['vocabulary_voice']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            voice_data = vocabulary_voice.read()
            query = """
                INSERT INTO vocabulary (topic_id, vocabulary_en, vocabulary_tw, PartOfSpeech, IPA, example, vocabulary_voice, class)
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
        # 获取现有主题列表
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

# 新增對話主題
@app.route('/add_conversation_topic', methods=['GET', 'POST'])
def add_conversation_topic():
    if request.method == 'POST':
        name = request.form['name']
        difficulty_class = request.form['class']
        character_name = request.form['character_name']
        icon_file = request.files['icon']

        if icon_file and allowed_file(icon_file.filename):
            try:
                connection = mysql.connector.connect(**config)
                cursor = connection.cursor()
                
                # 检查是否存在重复的 name 和 class
                check_query = "SELECT COUNT(*) FROM conversationTopic WHERE name = %s AND class = %s"
                cursor.execute(check_query, (name, difficulty_class))
                result = cursor.fetchone()
                
                if result[0] > 0:
                    flash('Topic with the same name and class already exists!', 'danger')
                else:
                    # 插入icon数据
                    icon_data = icon_file.read()
                    cursor.execute("INSERT INTO icon (icon) VALUES (%s)", (icon_data,))
                    icon_id = cursor.lastrowid

                    # 插入conversationTopic数据
                    query = "INSERT INTO conversationTopic (name, class, character_id, character_name) VALUES (%s, %s, %s, %s)"
                    cursor.execute(query, (name, difficulty_class, icon_id, character_name))
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
        else:
            flash('Invalid file type. Only JPG and PNG files are allowed.', 'danger')

        return redirect(url_for('add_conversation_topic'))
    return render_template('add_conversationTopic.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

# 新增對話內容
@app.route('/add_conversation', methods=['GET', 'POST'])
def add_conversation():
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        character_id = request.form.get('character_id', None)
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        difficulty_class = request.form['class']
        conversation_voice = request.files['conversation_voice']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            voice_data = conversation_voice.read()
            query = """
                INSERT INTO conversation (topic_id, character_id, conversation_en, conversation_tw, conversation_voice, class)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (topic_id, character_id, conversation_en, conversation_tw, voice_data, difficulty_class))
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

@app.route('/get_characters/<int:topic_id>')
def get_characters(topic_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        query = "SELECT character_id, character_name FROM conversationTopic WHERE id = %s"
        cursor.execute(query, (topic_id,))
        characters = cursor.fetchall()
        return jsonify(characters)
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return jsonify([])
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 列出所有單字主題
@app.route('/vocabulary_topics')
def vocabulary_topics():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, class FROM vocabularyTopic")
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

# 修改單字主題
@app.route('/edit_vocabulary_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_vocabulary_topic(topic_id):
    if request.method == 'POST':
        name = request.form['name']
        difficulty_class = request.form['class']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "UPDATE vocabularyTopic SET name = %s, class = %s WHERE id = %s"
            cursor.execute(query, (name, difficulty_class, topic_id))
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
            cursor.execute("SELECT id, name, class FROM vocabularyTopic WHERE id = %s", (topic_id,))
            topic = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topic = None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_vocabulary_topic.html', topic=topic)

# 刪除單字主題
@app.route('/delete_vocabulary_topic/<int:topic_id>')
def delete_vocabulary_topic(topic_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
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

# 列出所有對話主題
@app.route('/conversation_topics')
def conversation_topics():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, class FROM conversationTopic")
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

# 修改對話主題
@app.route('/edit_conversation_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_conversation_topic(topic_id):
    if request.method == 'POST':
        name = request.form['name']
        difficulty_class = request.form['class']
        character_name = request.form['character_name']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "UPDATE conversationTopic SET name = %s, class = %s, character_name = %s WHERE id = %s"
            cursor.execute(query, (name, difficulty_class, character_name, topic_id))
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
            cursor.execute("SELECT id, name, class, character_name FROM conversationTopic WHERE id = %s", (topic_id,))
            topic = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            topic = None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_conversation_topic.html', topic=topic)

# 刪除對話主題
@app.route('/delete_conversation_topic/<int:topic_id>')
def delete_conversation_topic(topic_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
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

# 列出所有單字
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

# 修改單字
@app.route('/edit_vocabulary/<int:vocabulary_id>', methods=['GET', 'POST'])
def edit_vocabulary(vocabulary_id):
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        vocabulary_en = request.form['vocabulary_en']
        vocabulary_tw = request.form['vocabulary_tw']
        part_of_speech = request.form['PartOfSpeech']
        ipa = request.form['IPA']
        example = request.form['example']
        difficulty_class = request.form['class']
        vocabulary_voice = request.files.get('vocabulary_voice')

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            if vocabulary_voice:
                voice_data = vocabulary_voice.read()
                query = """
                    UPDATE vocabulary SET topic_id = %s, vocabulary_en = %s, vocabulary_tw = %s, PartOfSpeech = %s, IPA = %s, example = %s, vocabulary_voice = %s, class = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, vocabulary_en, vocabulary_tw, part_of_speech, ipa, example, voice_data, difficulty_class, vocabulary_id))
            else:
                query = """
                    UPDATE vocabulary SET topic_id = %s, vocabulary_en = %s, vocabulary_tw = %s, PartOfSpeech = %s, IPA = %s, example = %s, class = %s
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
            cursor.execute("SELECT id, topic_id, vocabulary_en, vocabulary_tw, PartOfSpeech, IPA, example, class FROM vocabulary WHERE id = %s", (vocabulary_id,))
            vocabulary = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            vocabulary = None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_vocabulary.html', vocabulary=vocabulary)

# 刪除單字
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

# 列出所有對話
@app.route('/conversations')
def conversations():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, conversation_en, conversation_tw FROM conversation")
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

# 修改對話
@app.route('/edit_conversation/<int:conversation_id>', methods=['GET', 'POST'])
def edit_conversation(conversation_id):
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        character_id = request.form.get('character_id', None)
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        difficulty_class = request.form['class']
        conversation_voice = request.files.get('conversation_voice')

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            if conversation_voice:
                voice_data = conversation_voice.read()
                query = """
                    UPDATE conversation SET topic_id = %s, character_id = %s, conversation_en = %s, conversation_tw = %s, conversation_voice = %s, class = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, character_id, conversation_en, conversation_tw, voice_data, difficulty_class, conversation_id))
            else:
                query = """
                    UPDATE conversation SET topic_id = %s, character_id = %s, conversation_en = %s, conversation_tw = %s, class = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, character_id, conversation_en, conversation_tw, difficulty_class, conversation_id))
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
            cursor.execute("SELECT id, topic_id, character_id, conversation_en, conversation_tw, class FROM conversation WHERE id = %s", (conversation_id,))
            conversation = cursor.fetchone()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            conversation = None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_conversation.html', conversation=conversation)

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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
