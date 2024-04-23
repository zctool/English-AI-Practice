from flask import Flask, request, jsonify
from flask_cors import CORS 
from gtts import gTTS
import os
import io

app = Flask(__name__)
CORS(app)  # 使 Flask 应用支持跨域请求

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    user_text = data.get('text', '')

    bot_reply = 'Hello, you said: ' + user_text

    tts = gTTS(bot_reply, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    return jsonify({'reply': bot_reply, 'audio': mp3_fp.read().hex()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
