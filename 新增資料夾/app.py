import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from config import Config
from models import db, Topic, Vocabulary, VocabularyCollect

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    topics = Topic.query.all()
    return render_template('index.html', topics=topics)

@app.route('/words/<int:topic_id>')
def words(topic_id):
    words = Vocabulary.query.filter_by(topic_id=topic_id).all()
    return render_template('words.html', words=words)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 201

@app.route('/collect', methods=['POST'])
def collect():
    data = request.get_json()
    collect = VocabularyCollect(collect=data['collect'])
    db.session.add(collect)
    db.session.commit()
    return jsonify({'message': 'Vocabulary collected successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)
