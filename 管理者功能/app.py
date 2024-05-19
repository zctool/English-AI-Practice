from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 必须设置一个密钥用于闪现消息

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
@app.route('/add_vocabularyTopic', methods=['GET', 'POST'])
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
@app.route('/add_conversationTopic', methods=['GET', 'POST'])
def add_conversation_topic():
    if request.method == 'POST':
        name = request.form['name']
        difficulty_class = request.form['class']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            query = "INSERT INTO conversationTopic (name, class) VALUES (%s, %s)"
            cursor.execute(query, (name, difficulty_class))
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

# 新增對話內容
@app.route('/add_conversation', methods=['GET', 'POST'])
def add_conversation():
    if request.method == 'POST':
        topic_id = request.form['topic_id']
        charath_id = request.form['charath_id']
        charather_name = request.form['charather_name']
        conversation_en = request.form['conversation_en']
        conversation_tw = request.form['conversation_tw']
        difficulty_class = request.form['class']
        conversation_voice = request.files['conversation_voice']

        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            voice_data = conversation_voice.read()
            query = """
                INSERT INTO conversation (topic_id, charath_id, charather_name, conversation_en, conversation_tw, conversation_voice, class)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (topic_id, charath_id, charather_name, conversation_en, conversation_tw, voice_data, difficulty_class))
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
        # 获取现有主题列表
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
