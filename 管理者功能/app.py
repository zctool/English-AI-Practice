from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
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

# 新增單字主題
@app.route('/add_vocabulary_topic', methods=['GET', 'POST'])
def add_vocabulary_topic():
    if request.method == 'POST':
        name = request.form['name']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "INSERT INTO vocabularyTopic (name) VALUES (%s)"
            cursor.execute(query, (name,))
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

# 查看和编辑单字主题
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

# 编辑单字主题
@app.route('/edit_vocabulary_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_vocabulary_topic(topic_id):
    if request.method == 'POST':
        name = request.form['name']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "UPDATE vocabularyTopic SET name = %s WHERE id = %s"
            cursor.execute(query, (name, topic_id))
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
            cursor.execute("SELECT id, name FROM vocabularyTopic WHERE id = %s", (topic_id,))
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

# 删除单字主题
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

# 查看和编辑单字
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

# 编辑单字
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

# 删除单字
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
        difficulty_class = request.form['class']

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
                # 插入conversationTopic数据
                query = "INSERT INTO conversationTopic (name, class) VALUES (%s, %s)"
                cursor.execute(query, (name, difficulty_class))
                topic_id = cursor.lastrowid

                # 插入人物数据
                character_names = request.form.getlist('character_name')
                icons = request.files.getlist('icon')

                for i in range(len(character_names)):
                    character_name = character_names[i]
                    icon_file = icons[i]

                    if icon_file and allowed_file(icon_file.filename):
                        icon_data = icon_file.read()
                        cursor.execute("INSERT INTO icon (icon) VALUES (%s)", (icon_data,))
                        icon_id = cursor.lastrowid

                        # 将人物和话题关联
                        cursor.execute("INSERT INTO characters (character_name, icon_id, topic_id) VALUES (%s, %s, %s)", (character_name, icon_id, topic_id))

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

# 新增对话内容
@app.route('/add_conversation', methods=['GET', 'POST'])
def add_conversation():
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        character_id = request.form['character_id']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        difficulty_class = request.form['class']
        conversation_voice = request.files['conversation_voice']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()

            # 检查是否存在相同 topic_id 和 class 的对话内容
            check_query = "SELECT COUNT(*) FROM conversation WHERE topic_id = %s AND class = %s"
            cursor.execute(check_query, (topic_id, difficulty_class))
            result = cursor.fetchone()

            if result[0] > 0:
                flash('Conversation with the same topic and class already exists!', 'danger')
            else:
                voice_data = conversation_voice.read()
                query = """
                    INSERT INTO conversation (topic_id, character_id, conversation_en, conversation_tw, class, conversation_voice)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (topic_id, character_id, conversation_en, conversation_tw, difficulty_class, voice_data))
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

@app.route('/get_characters/<int:topic_id>/<string:difficulty_class>', methods=['GET'])
def get_characters(topic_id, difficulty_class):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        query = """
            SELECT characters.id, characters.character_name 
            FROM characters 
            JOIN conversationTopic ON characters.topic_id = conversationTopic.id 
            WHERE characters.topic_id = %s AND conversationTopic.class = %s
        """
        cursor.execute(query, (topic_id, difficulty_class))
        characters = cursor.fetchall()
        return jsonify(characters)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 查看和编辑对话主题
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

# 编辑对话主题
@app.route('/edit_conversation_topic/<int:topic_id>', methods=['GET', 'POST'])
def edit_conversation_topic(topic_id):
    if request.method == 'POST':
        name = request.form['name']
        difficulty_class = request.form['class']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "UPDATE conversationTopic SET name = %s, class = %s WHERE id = %s"
            cursor.execute(query, (name, difficulty_class, topic_id))
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
            cursor.execute("SELECT id, name, class FROM conversationTopic WHERE id = %s", (topic_id,))
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

# 删除对话主题
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

# 查看和编辑对话
@app.route('/conversations')
def conversations():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, topic_id, conversation_en, conversation_tw FROM conversation")
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

# 编辑对话
@app.route('/edit_conversation/<int:conversation_id>', methods=['GET', 'POST'])
def edit_conversation(conversation_id):
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        conversation_voice = request.files.get('conversation_voice')

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            if conversation_voice:
                voice_data = conversation_voice.read()
                query = """
                    UPDATE conversation SET topic_id = %s, conversation_en = %s, conversation_tw = %s, conversation_voice = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, conversation_en, conversation_tw, voice_data, conversation_id))
            else:
                query = """
                    UPDATE conversation SET topic_id = %s, conversation_en = %s, conversation_tw = %s
                    WHERE id = %s
                """
                cursor.execute(query, (topic_id, conversation_en, conversation_tw, conversation_id))
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
            cursor.execute("SELECT id, topic_id, conversation_en, conversation_tw FROM conversation WHERE id = %s", (conversation_id,))
            conversation = cursor.fetchone()
            cursor.execute("SELECT id, name FROM conversationTopic")
            topics = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            conversation = None
            topics = []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        return render_template('edit_conversation.html', conversation=conversation, topics=topics)

# 删除对话
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

# 查看和编辑人物
@app.route('/characters/<int:topic_id>')
def characters(topic_id):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT id, character_name FROM characters WHERE topic_id = %s", (topic_id,))
        characters = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        characters = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('characters.html', characters=characters, topic_id=topic_id)

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
        return redirect(url_for('characters', topic_id=request.form['topic_id']))
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
        return render_template('edit_character.html', character=character, topic_id=request.args.get('topic_id'))

# 删除人物
@app.route('/delete_character/<int:character_id>/<int:topic_id>')
def delete_character(character_id, topic_id):
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
    return redirect(url_for('characters', topic_id=topic_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
