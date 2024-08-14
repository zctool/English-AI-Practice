import io
from flask import Blueprint, jsonify, render_template, request, redirect, send_file, url_for, flash, g, session
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
from flask import flash, redirect, render_template, request, url_for, session
import mysql.connector
import os
from werkzeug.utils import secure_filename

# 課程上傳功能
UPLOAD_FOLDER = 'static/uploads'  # 可選，用於保存文件的本地備份
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

@teacher_bp.route('/upload_course', methods=['GET', 'POST'])
@teacher_required
def upload_course():
    if request.method == 'POST':
        course_name = request.form['course_name']
        course_type = request.form['course_type']
        sentences = request.form.getlist('sentence')
        audios = request.files.getlist('audio')
        is_open = 'is_open' in request.form

        if len(sentences) != len(audios):
            flash('每句話都需要上傳對應的音頻。')
            return redirect(request.url)

        try:
            # 使用配置创建数据库连接
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
            for idx, audio in enumerate(audios):
                if audio and allowed_file(audio.filename):
                    filename = secure_filename(audio.filename)
                    audio_data = audio.read()  # 读取文件的二进制数据

                    add_sentence = """
                        INSERT INTO Sentence (content, course_id, audio_file)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(add_sentence, (sentences[idx], course_id, audio_data))
                else:
                    flash('音頻文件格式不支持。')
                    return redirect(request.url)

            connection.commit()
            flash('課程上傳成功。')

        except mysql.connector.Error as err:
            # 捕捉資料庫錯誤，並顯示錯誤信息
            connection.rollback()
            flash(f'資料庫錯誤: {err}', 'danger')
            print(f"資料庫錯誤: {err}")  # 或者使用 logging 模組來記錄錯誤信息

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for('teacher.upload_course'))
    return render_template('upload_course.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

##查詢、刪除課程
@teacher_bp.route('/manage_courses', methods=['GET', 'POST'])
@teacher_required
def manage_courses():
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        # 查詢老师所创建的所有课程
        teacher_email = session.get('email')
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


teacher_bp.add_url_rule('/edit_course_content/<int:course_id>', 'edit_course_content', edit_course_content)
teacher_bp.add_url_rule('/get_audio/<int:sentence_id>', 'get_audio', get_audio)
teacher_bp.add_url_rule('/delete_sentence/<int:sentence_id>', 'delete_sentence', delete_sentence)
teacher_bp.add_url_rule('/manage_courses', 'manage_courses', manage_courses)
teacher_bp.add_url_rule('/edit_course/<int:course_id>', 'edit_course', edit_course)


