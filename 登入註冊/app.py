from flask import Flask, request, jsonify, redirect, url_for
import yaml
import mysql.connector

app = Flask(__name__)

# Load DB config from a YAML file
db_config = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
config = {
    'user': db_config['MYSQL_USER'],
    'password': db_config['MYSQL_PASSWORD'],
    'host': db_config['MYSQL_HOST'],
    'database': db_config['MYSQL_DB'],
    'raise_on_warnings': True
}

@app.route('/register', methods=['POST'])
def register():
    user_details = request.form
    username = user_details['username']
    email = user_details['email']
    password = user_details['pwd']
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    cur.execute("INSERT INTO users(username, email, pwd) VALUES (%s, %s, %s)", (username, email, password))
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
    cur.execute("SELECT * FROM users WHERE username = %s AND pwd = %s", (username, password))
    result_value = cur.fetchone()
    cur.close()
    conn.close()
    if result_value:
        return 'Logged in successfully'
    else:
        return 'Username or Password is wrong'

if __name__ == '__main__':
    app.run(debug=True)
