from flask import Flask, request, jsonify, redirect, url_for
import mysql.connector
import pymysql

app = Flask(__name__)

config=pymysql.connect(
            user='case113201',
            password='@Ntub_113201',
            port='3306',
            host='140.131.114.242',
            auth_plugin='mysql_native_password'
)

@app.route('/register', methods=['POST'])
def register():
    user_details = request.form
    username = user_details['username']
    email = user_details['email']
    password = user_details['pwd']
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    cur.execute("INSERT INTO users(username, email, pwd) VALUES (%s, %s, %s);", (username, email, password))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('login'))

@app.route('/login', methods=['POST'])
def login():
    user_details = request.form
    username = user_details['username']
    password = user_details['pwd']
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND pwd = %s;", (username, password))
    result_value = cur.fetchone()
    cur.close()
    conn.close()
    if result_value:
        return 'Logged in successfully'
    else:
        return 'Username or Password is wrong'

if __name__ == '__main__':
    app.run(debug=True)
