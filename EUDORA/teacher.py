import io
from flask import Blueprint, abort, jsonify, render_template, request, redirect, send_file, url_for, flash, g, session
import mysql.connector
from functools import wraps
from werkzeug.utils import secure_filename
import os


teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
teacher_bp.secret_key = 'your_secret_key'

# MySQL 数据库连接配置
config = {
    'user': 'case113201',
    'password': '@Ntub_113201',
    'host': '140.131.114.242',
    'database': '113-NTUB',
}

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('email') or session.get('role') != 'teacher':
            flash('You do not have access to this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('teacher.teacher_index'))

@teacher_bp.route('/')
@teacher_required
def teacher_index():
    return render_template('teacher_home.html')


### 課程上傳功能 ###
import torch
from flask import flash, redirect, render_template, request, url_for, session
import mysql.connector
from werkzeug.utils import secure_filename
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import io
import soundfile as sf

# 課程上傳功能相關配置
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

device = "cpu"
if torch.cuda.is_available():
    device = "cuda"

# 加載 TTS 模型和 Tokenizer
model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler_tts_mini_v0.1").to(device)
tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler_tts_mini_v0.1")

# 定義聲音描述類型
VOICE_TYPES = {
    "gentle_male": "A gentle male voice, slightly deep, calm and comforting.",
    "gentle_female": "A gentle female voice, soothing, soft and clear.",
    "energetic_male": "An energetic male voice, enthusiastic, bright and engaging.",
    "energetic_female": "An energetic female voice, high-pitched, lively and dynamic.",
    "warm_male": "A warm male voice, slightly raspy, with a comforting and friendly tone.",
    "warm_female": "A warm female voice, with a kind, approachable and gentle tone.",
    "professional_male": "A professional male voice, authoritative, confident and clear.",
    "professional_female": "A professional female voice, clear, concise and firm.",
    "whispering_male": "A whispering male voice, quiet, soft and mysterious.",
    "whispering_female": "A whispering female voice, gentle, hushed and soothing.",
    "bright_male": "A bright male voice, cheerful, positive and vibrant.",
    "bright_female": "A bright female voice, uplifting, happy and spirited.",
    "calm_male": "A calm male voice, steady, composed and relaxed.",
    "calm_female": "A calm female voice, serene, peaceful and gentle.",
    "excited_male": "An excited male voice, animated, enthusiastic and lively.",
    "excited_female": "An excited female voice, highly expressive, upbeat and joyful.",
    "deep_male": "A deep male voice, resonant, powerful and mature.",
    "deep_female": "A deep female voice, rich, mature and captivating.",
    "soft_male": "A soft male voice, delicate, gentle and smooth.",
    "soft_female": "A soft female voice, tender, light and graceful."
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_audio(sentence, voice_type):
    """生成音頻並返回其二進制數據"""
    description = VOICE_TYPES.get(voice_type, "A gentle male voice, slightly deep, calm and comforting.")
    
    # 生成输入的 input_ids 和 attention_mask
    encoded_input = tokenizer(description, return_tensors="pt", padding=True)
    input_ids = encoded_input.input_ids.to(device)
    attention_mask = encoded_input.attention_mask.to(device)

    # 生成 prompt 的 input_ids 和 attention_mask
    prompt_encoded_input = tokenizer(sentence, return_tensors="pt", padding=True)
    prompt_input_ids = prompt_encoded_input.input_ids.to(device)
    prompt_attention_mask = prompt_encoded_input.attention_mask.to(device)

    # 生成音频时传递 attention_mask 和 prompt_attention_mask
    generation = model.generate(
        input_ids=input_ids, 
        attention_mask=attention_mask,  # 传递主 input 的 attention_mask
        prompt_input_ids=prompt_input_ids,
        prompt_attention_mask=prompt_attention_mask  # 为 prompt 传递 attention_mask
    ).to(torch.float32)

    audio_arr = generation.cpu().numpy().squeeze()

    # 将音频数据转为二进制数据
    audio_bytes = io.BytesIO()
    sf.write(audio_bytes, audio_arr, model.config.sampling_rate, format='wav')
    audio_bytes.seek(0)  # 重置流的位置

    return audio_bytes.read()

@teacher_bp.route('/upload_course', methods=['GET', 'POST'])
@teacher_required
def upload_course():
    if request.method == 'POST':
        course_name = request.form['course_name']
        course_type = request.form['course_type']
        sentences = request.form.getlist('sentence')
        voice_types = request.form.getlist('voice_type')  # 獲取每句句子對應的聲音類型
        is_open = 'is_open' in request.form

        try:
            # 使用配置創建數據庫連接
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()

            # 獲取上傳課程的老師Email
            teacher_email = session.get('email')

            # 插入課程信息
            add_course = """
                INSERT INTO Course (name, type, teacher_email, is_open)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(add_course, (course_name, course_type, teacher_email, is_open))
            course_id = cursor.lastrowid

            # 插入句子和音頻信息
            for sentence, voice_type in zip(sentences, voice_types):
                # 生成音頻並返回其二進制數據
                audio_data = generate_audio(sentence, voice_type)

                add_sentence = """
                    INSERT INTO Sentence (content, course_id, audio_file)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(add_sentence, (sentence, course_id, audio_data))

            connection.commit()
            flash('課程上傳成功。', 'success')

        except mysql.connector.Error as err:
            connection.rollback()
            flash(f'資料庫錯誤: {err}', 'danger')
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for('teacher.upload_course'))
    return render_template('upload_course.html', voice_types=VOICE_TYPES)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 管理课程（查詢、刪除）
@teacher_bp.route('/manage_courses', methods=['GET', 'POST'])
def manage_courses():
    connection = None
    cursor = None
    try:
        # 确保用户是已登录的教师
        if 'email' not in session or session.get('role') != 'teacher':
            abort(403)

        # 建立数据库连接
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        # 获取当前教师的 email
        teacher_email = session.get('email')

        # 查询该教师所创建的所有课程
        query = "SELECT * FROM Course WHERE teacher_email = %s"
        cursor.execute(query, (teacher_email,))
        courses = cursor.fetchall()

        # 处理课程删除请求
        if request.method == 'POST':
            if 'delete_course' in request.form:
                course_id = request.form['course_id']
                delete_query = "DELETE FROM Course WHERE id = %s AND teacher_email = %s"
                cursor.execute(delete_query, (course_id, teacher_email))
                connection.commit()
                flash('課程已成功刪除', 'success')
                return redirect(url_for('teacher.manage_courses'))

    except mysql.connector.Error as err:
        flash(f'資料庫錯誤: {err}', 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('manage_courses.html', courses=courses)

##編輯課程

@teacher_bp.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@teacher_required
def edit_course(course_id):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        # 獲取課程信息
        teacher_email = session.get('email')
        query = "SELECT * FROM Course WHERE id = %s AND teacher_email = %s"
        cursor.execute(query, (course_id, teacher_email))
        course = cursor.fetchone()

        if not course:
            flash('未找到課程或您無權編輯該課程', 'danger')
            return redirect(url_for('teacher.manage_courses'))

        if request.method == 'POST':
            # 更新課程信息
            course_name = request.form['course_name']
            course_type = request.form['course_type']
            is_open = 'is_open' in request.form

            update_query = """
                UPDATE Course
                SET name = %s, type = %s, is_open = %s
                WHERE id = %s AND teacher_email = %s
            """
            cursor.execute(update_query, (course_name, course_type, is_open, course_id, teacher_email))
            connection.commit()
            flash('課程更新成功', 'success')
            return redirect(url_for('teacher.manage_courses'))

    except mysql.connector.Error as err:
        flash(f'資料庫錯誤: {err}', 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('edit_course.html', course=course)

##編輯課文內容

@teacher_bp.route('/edit_course_content/<int:course_id>', methods=['GET', 'POST'])
@teacher_required
def edit_course_content(course_id):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        # 獲取課程信息
        teacher_email = session.get('email')
        query = "SELECT * FROM Course WHERE id = %s AND teacher_email = %s"
        cursor.execute(query, (course_id, teacher_email))
        course = cursor.fetchone()

        if not course:
            flash('未找到課程或您無權編輯該課程', 'danger')
            return redirect(url_for('teacher.manage_courses'))

        # 獲取課程內的句子和音頻信息
        query = "SELECT * FROM Sentence WHERE course_id = %s"
        cursor.execute(query, (course_id,))
        sentences = cursor.fetchall()

        if request.method == 'POST':
            # 更新句子和音頻信息
            sentence_ids = request.form.getlist('sentence_id')
            new_sentences = request.form.getlist('sentence')
            new_audios = request.files.getlist('audio')

            for idx, sentence_id in enumerate(sentence_ids):
                if sentence_id:
                    # 更新已存在的句子
                    update_sentence = """
                        UPDATE Sentence
                        SET content = %s
                        WHERE id = %s AND course_id = %s
                    """
                    cursor.execute(update_sentence, (new_sentences[idx], sentence_id, course_id))

                    # 如果有新音頻，則更新音頻文件
                    if new_audios[idx]:
                        audio_data = new_audios[idx].read()
                        update_audio = """
                            UPDATE Sentence
                            SET audio_file = %s
                            WHERE id = %s AND course_id = %s
                        """
                        cursor.execute(update_audio, (audio_data, sentence_id, course_id))

                else:
                    # 插入新句子
                    audio_data = new_audios[idx].read() if new_audios[idx] else None
                    insert_sentence = """
                        INSERT INTO Sentence (content, course_id, audio_file)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_sentence, (new_sentences[idx], course_id, audio_data))

            connection.commit()
            flash('課程內容更新成功', 'success')
            return redirect(url_for('teacher.edit_course_content', course_id=course_id))

    except mysql.connector.Error as err:
        flash(f'資料庫錯誤: {err}', 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('edit_course_content.html', course=course, sentences=sentences)

##獲取音檔

@teacher_bp.route('/get_audio/<int:sentence_id>')
@teacher_required
def get_audio(sentence_id):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT audio_file FROM Sentence WHERE id = %s"
        cursor.execute(query, (sentence_id,))
        sentence = cursor.fetchone()

        if not sentence or not sentence['audio_file']:
            flash('未找到音頻文件', 'danger')
            return '', 404

        return send_file(io.BytesIO(sentence['audio_file']), mimetype='audio/mp3')

    except mysql.connector.Error as err:
        flash(f'資料庫錯誤: {err}', 'danger')
        return '', 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

##刪除課程內容

@teacher_bp.route('/delete_sentence/<int:sentence_id>')
@teacher_required
def delete_sentence(sentence_id):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        delete_query = "DELETE FROM Sentence WHERE id = %s"
        cursor.execute(delete_query, (sentence_id,))
        connection.commit()

        flash('句子已成功刪除', 'success')
    except mysql.connector.Error as err:
        flash(f'資料庫錯誤: {err}', 'danger')
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(request.referrer or url_for('teacher.manage_courses'))

# 老师查看所有学生成绩
@teacher_bp.route('/learning_progress', methods=['GET', 'POST']) 
@teacher_required
def teacher_learning_progress():
    user_email = session.get('email')
    
    if not user_email:
        return jsonify({'error': '未登录'}), 401

    # 使用配置创建数据库连接
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    # 获取老师教过的所有学生
    cursor.execute("""
        SELECT DISTINCT u.id, u.userName
        FROM UserRecordings r
        JOIN Sentence s ON r.sentence_id = s.id
        JOIN users u ON r.user_id = u.id
        JOIN Course c ON s.course_id = c.id
        WHERE c.teacher_email = %s
    """, (user_email,))
    students = cursor.fetchall()

    # 初始化数据结构，确保即使没有选择学生或句子时也有默认值
    data = {
        'students': students,
        'current_student': None,
        'sentences': [],
        'current_sentence': None,
        'dates': [],
        'scores': [],
        'student_name': None
    }

    # 获取当前选中的学生 ID 和句子 ID
    student_id = request.form.get('student_id')
    sentence_id = request.form.get('sentence_id')

    # 如果选择了学生 ID，查询该学生的信息
    if student_id:
        # 获取该学生的名字
        cursor.execute("SELECT userName FROM users WHERE id = %s", (student_id,))
        student_name = cursor.fetchone()['userName']

        # 获取该学生学过的句子，且这些句子属于该老师的课程
        cursor.execute("""
            SELECT DISTINCT s.id, s.content
            FROM UserRecordings r
            JOIN Sentence s ON r.sentence_id = s.id
            JOIN Course c ON s.course_id = c.id
            WHERE r.user_id = %s AND c.teacher_email = %s
        """, (student_id, user_email))
        sentences = cursor.fetchall()

        # 如果没有选择句子，默认选择第一个句子
        if not sentence_id and sentences:
            sentence_id = sentences[0]['id']

        # 获取该学生选择的句子的学习记录
        if sentence_id:
            cursor.execute("""
                SELECT s.content AS sentence_text, r.recording_date, 
                       (r.similarity_score * 0.1 + r.text_similarity * 0.9) * 100 AS score 
                FROM UserRecordings r
                JOIN Sentence s ON r.sentence_id = s.id
                WHERE r.user_id = %s AND s.id = %s
                ORDER BY r.recording_date
            """, (student_id, sentence_id))
            results = cursor.fetchall()

            # 更新数据字典
            data['current_student'] = student_id
            data['sentences'] = sentences
            data['current_sentence'] = sentence_id
            data['student_name'] = student_name

            # 将查询结果转换为图表数据
            for row in results:
                data['dates'].append(row['recording_date'].strftime('%Y-%m-%d'))
                data['scores'].append({
                    'score': round(row['score'], 2),
                    'label': f"{student_name} - {round(row['score'], 2)}%"  # 包含学生名字和分数的标签
                })

    cursor.close()
    connection.close()

    return render_template('teacher_learning_progress.html', data=data)

teacher_bp.add_url_rule('/edit_course_content/<int:course_id>', 'edit_course_content', edit_course_content)
teacher_bp.add_url_rule('/get_audio/<int:sentence_id>', 'get_audio', get_audio)
teacher_bp.add_url_rule('/delete_sentence/<int:sentence_id>', 'delete_sentence', delete_sentence)
teacher_bp.add_url_rule('/manage_courses', 'manage_courses', manage_courses)
teacher_bp.add_url_rule('/edit_course/<int:course_id>', 'edit_course', edit_course)


