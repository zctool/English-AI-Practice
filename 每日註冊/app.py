# app.py
from flask import Flask, request, jsonify
import mysql.connector
import datetime

app = Flask(__name__)

config = {
    'user': 'case113201',
    'password': '@Ntub_113201',
    'host': '140.131.114.242',
    'database': '113-NTUB',
    'raise_on_warnings': True
}

@app.route('/113-NTUB', methods=['POST'])
def signin():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    today = datetime.date.today()
    query = 'INSERT INTO signins (sign_date) VALUES (%s)'
    try:
        cursor.execute(query, (today,))
        conn.commit()
        message = '簽到成功！'
    except mysql.connector.Error as err:
        message = '今日已經簽到過了！'
    cursor.close()
    conn.close()
    return jsonify({'message': message})

if __name__ == '__main__':
    app.run(debug=True)
