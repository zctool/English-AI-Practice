import pymysql
from flask import Flask, jsonify

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(host='localhost',
                           user='your_username',
                           password='your_password',
                           db='conversation_db',
                           cursorclass=pymysql.cursors.DictCursor)

@app.route('/conversation/<topic>')
def get_conversation(topic):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT t.name, c.speaker, c.line FROM topics t JOIN conversations c ON t.id = c.topic_id WHERE t.name = %s', (topic,))
    conversations = cursor.fetchall()
    cursor.close()
    conn.close()
    if conversations:
        return jsonify(conversations)
    else:
        return jsonify([]), 404

if __name__ == '__main__':
    app.run(debug=True)
