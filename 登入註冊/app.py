from flask import Flask, request, jsonify, redirect, url_for
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)

# Load DB config from a YAML file
db_config = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
app.config['MYSQL_HOST'] = db_config['140.131.114.242']
app.config['MYSQL_USER'] = db_config['case113201']
app.config['MYSQL_PASSWORD'] = db_config['@Ntub_113201']
app.config['MYSQL_DB'] = db_config['113-NTUB']

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    user_details = request.form
    username = user_details['username']
    email = user_details['email']
    password = user_details['password']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(username, email, password) VALUES (%s, %s, %s)", (username, email, password))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('login'))

@app.route('/login', methods=['POST'])
def login():
    user_details = request.form
    username = user_details['username']
    password = user_details['password']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    if result_value > 0:
        return 'Logged in successfully'
    else:
        return 'Username or Password is wrong'

if __name__ == '__main__':
    app.run(debug=True)
