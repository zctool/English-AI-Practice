import os
import requests
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from mysql.connector import pooling, Error

app = Flask(__name__)
app.secret_key = os.urandom(24)

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

def execute_query(query, params=None):
    try:
        conn = cnxpool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return results
    except Error as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('main'))
    return render_template('index.html')

@app.route('/login/token', methods=['POST'])
def login_token():
    token = request.json.get('id_token')
    userinfo_response = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": token}
    )
    userinfo = userinfo_response.json()

    if userinfo.get('email_verified'):
        users_email = userinfo['email']
        users_name = userinfo['name']
        picture = userinfo['picture']

        session['email'] = users_email
        session['name'] = users_name

        user = execute_query("SELECT * FROM users WHERE GoogleEmail = %s", (users_email,))

        if not user:
            return jsonify({'register_required': True})

        session['role'] = user[0]['role']

        if session['role'] == 'admin':
            return jsonify({'redirect_url': url_for('admin.admin_index')})
        elif session['role'] == 'teacher':
            return jsonify({'redirect_url': url_for('teacher.teacher_index')})
        else:
            return jsonify({'redirect_url': url_for('main')})
    else:
        return jsonify({'error': '用戶身份驗證失敗'}), 400

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    icon = request.files['icon'].read() if 'icon' in request.files else None

    conn = cnxpool.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (userName, GoogleEmail, icon, role) VALUES (%s, %s, %s, 'user')", (username, email, icon))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('main'))

@app.route('/main')
def main():
    if 'email' not in session:
        return redirect(url_for('index'))

    user_email = session['email']
    user = execute_query("SELECT userName, role FROM users WHERE GoogleEmail = %s", (user_email,))[0]

    if user['role'] == 'admin':
        return redirect(url_for('admin.admin_index'))
    elif user['role'] == 'teacher':
        return redirect(url_for('teacher.teacher_index'))
    else:
        return render_template('main.html', name=user['userName'], email=user_email)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
