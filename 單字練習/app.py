from flask import Flask, jsonify, request
import pymysql

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(host='localhost',
                           user='your_username',
                           password='your_password',
                           db='conversation_db',
                           cursorclass=pymysql.cursors.DictCursor)

@app.route('/vocabulary')
def get_vocabulary():
    keyword = request.args.get('keyword')
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM vocabulary WHERE word LIKE %s'
    cursor.execute(query, ('%' + keyword + '%',))
    words = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(words)

if __name__ == '__main__':
    app.run(debug=True)
