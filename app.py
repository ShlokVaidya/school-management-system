from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import mysql.connector
import config
import os

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'public'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/public/<path:filename>')
def public_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'public'), filename)

def get_db():
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    return conn

def check_role(role):
    if 'user_id' not in session:
        return False
    if session['role'] != role:
        return False
    return True

def is_full_access():
    if 'user_id' not in session:
        return False
    return session.get('role') in ('admin', 'vice_principal', 'coordinator')

def check_teacher_access():
    if 'user_id' not in session:
        return False
    return session.get('role') in ('teacher', 'admin', 'vice_principal', 'coordinator')

def get_teacher_sections(teacher_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT section_id FROM teacher_sections WHERE teacher_id=%s", (teacher_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r['section_id'] for r in rows]

def get_teacher_subjects(teacher_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT subject_name FROM teacher_subjects WHERE teacher_id=%s", (teacher_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r['subject_name'] for r in rows]

def allowed_section_ids():
    if is_full_access():
        return [], True
    if session.get('role') == 'teacher':
        return get_teacher_sections(session['user_id']), False
    return [], False

def allowed_subjects():
    if is_full_access():
        return [], True
    if session.get('role') == 'teacher':
        return get_teacher_subjects(session['user_id']), False
    return [], False

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                session['user_id']   = user['id']
                session['role']      = user['role']
                session['full_name'] = user['full_name']
                return redirect(url_for('dashboard'))
            else:
                error = 'Wrong username or password!'
        except Exception as e:
            error = 'Database error: ' + str(e)
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session['role']
    if role in ('admin', 'vice_principal', 'coordinator'):
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if not is_full_access():
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role='teacher'")
    teacher_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM sections")
    section_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM students")
    student_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM assignments")
    assignment_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM marks")
    marks_count = cursor.fetchone()['cnt']

    cursor.execute("""
        SELECT a.*, u.full_name as posted_by_name
        FROM announcements a
        JOIN users u ON a.posted_by = u.id
        ORDER BY a.created_at DESC LIMIT 5
    """)
    notices = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html',
        teacher_count=teacher_count,
        section_count=section_count,
        student_count=student_count,
        assignment_count=assignment_count,
        marks_count=marks_count,
        notices=notices
    )

@app.route('/admin/teachers')
def admin_teachers():
    if not is_full_access():
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role = 'teacher' ORDER BY full_name")
    teachers = cursor.fetchall()

    for t in teachers:
        cursor.execute("""
            SELECT s.section_name FROM teacher_sections ts
            JOIN sections s ON ts.section_id = s.id
            WHERE ts.teacher_id = %s
            ORDER BY s.section_name
        """, (t['id'],))
        t['section_names'] = [r['section_name'] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT subject_name FROM teacher_subjects WHERE teacher_id = %s ORDER BY subject_name",
            (t['id'],)
        )
        t['subject_names'] = [r['subject_name'] for r in cursor.fetchall()]

    cursor.close()
    conn.close()
    return render_template('admin_teachers.html', teachers=teachers)

@app.route('/admin/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if not is_full_access():
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sections ORDER BY section_name")
    sections = cursor.fetchall()
    cursor.execute("SELECT * FROM subjects ORDER BY subject_name")
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    msg = ''
    if request.method == 'POST':
        full_name  = request.form['full_name']
        username   = request.form['username']
        password   = request.form['password']
        section_ids = request.form.getlist('section_ids')
        subject_names = request.form.getlist('subject_names')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, 'teacher', %s)",
                (username, password, full_name)
            )
            new_teacher_id = cursor.lastrowid

            for sid in section_ids:
                cursor.execute(
                    "INSERT IGNORE INTO teacher_sections (teacher_id, section_id) VALUES (%s, %s)",
                    (new_teacher_id, sid)
                )
            for sub in subject_names:
                cursor.execute(
                    "INSERT IGNORE INTO teacher_subjects (teacher_id, subject_name) VALUES (%s, %s)",
                    (new_teacher_id, sub)
                )

            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Teacher added with ' + str(len(section_ids)) + ' section(s) and ' + str(len(subject_names)) + ' subject(s).'
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('add_teacher.html', sections=sections, subjects=subjects, msg=msg)


@app.route('/admin/edit_teacher/<int:tid>', methods=['GET', 'POST'])
def edit_teacher(tid):
    if not is_full_access():
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'teacher'", (tid,))
    teacher = cursor.fetchone()
    cursor.execute("SELECT * FROM sections ORDER BY section_name")
    sections = cursor.fetchall()
    cursor.execute("SELECT * FROM subjects ORDER BY subject_name")
    subjects = cursor.fetchall()

    cursor.execute("SELECT section_id FROM teacher_sections WHERE teacher_id = %s", (tid,))
    assigned_section_ids = [r['section_id'] for r in cursor.fetchall()]
    cursor.execute("SELECT subject_name FROM teacher_subjects WHERE teacher_id = %s", (tid,))
    assigned_subjects = [r['subject_name'] for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    if not teacher:
        return "Teacher not found!"

    msg = ''
    if request.method == 'POST':
        full_name     = request.form['full_name']
        username      = request.form['username']
        password      = request.form['password']
        section_ids   = request.form.getlist('section_ids')
        subject_names = request.form.getlist('subject_names')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET full_name=%s, username=%s, password=%s WHERE id=%s",
                (full_name, username, password, tid)
            )
            cursor.execute("DELETE FROM teacher_sections WHERE teacher_id = %s", (tid,))
            cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = %s", (tid,))

            for sid in section_ids:
                cursor.execute(
                    "INSERT IGNORE INTO teacher_sections (teacher_id, section_id) VALUES (%s, %s)",
                    (tid, sid)
                )
            for sub in subject_names:
                cursor.execute(
                    "INSERT IGNORE INTO teacher_subjects (teacher_id, subject_name) VALUES (%s, %s)",
                    (tid, sub)
                )

            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Teacher updated!'
            assigned_section_ids = [int(x) for x in section_ids]
            assigned_subjects    = list(subject_names)
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('edit_teacher.html',
        teacher=teacher, sections=sections, subjects=subjects,
        assigned_section_ids=assigned_section_ids,
        assigned_subjects=assigned_subjects, msg=msg)


@app.route('/admin/delete_teacher/<int:tid>')
def delete_teacher(tid):
    if not is_full_access():
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE assignments SET teacher_id = NULL WHERE teacher_id = %s", (tid,))
        cursor.execute("DELETE FROM teacher_sections WHERE teacher_id = %s", (tid,))
        cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = %s", (tid,))
        cursor.execute("DELETE FROM users WHERE id = %s AND role = 'teacher'", (tid,))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass 
    return redirect(url_for('admin_teachers'))

@app.route('/admin/sections')
def admin_sections():
    if not is_full_access():
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, COUNT(st.id) as student_count
        FROM sections s
        LEFT JOIN students st ON st.section_id = s.id
        GROUP BY s.id
    """)
    sections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_sections.html', sections=sections)

@app.route('/admin/add_section', methods=['GET', 'POST'])
def add_section():
    if not is_full_access():
        return redirect(url_for('login'))
    msg = ''
    if request.method == 'POST':
        section_name = request.form['section_name']
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sections (section_name) VALUES (%s)", (section_name,))
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Section ' + section_name + ' added!'
        except Exception as e:
            msg = 'Error: ' + str(e)
    return render_template('add_section.html', msg=msg)

@app.route('/admin/edit_section/<int:sid>', methods=['GET', 'POST'])
def edit_section(sid):
    if not is_full_access():
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sections WHERE id = %s", (sid,))
    section = cursor.fetchone()
    cursor.close()
    conn.close()

    if not section:
        return "Section not found!"

    msg = ''
    if request.method == 'POST':
        new_name = request.form['section_name']
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE sections SET section_name = %s WHERE id = %s", (new_name, sid))
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Section updated!'
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('edit_section.html', section=section, msg=msg)

@app.route('/admin/delete_section/<int:sid>')
def delete_section(sid):
    if not is_full_access():
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sections WHERE id = %s", (sid,))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    return redirect(url_for('admin_sections'))

@app.route('/admin/students')
def admin_all_students():
    if not is_full_access():
        return redirect(url_for('login'))

    search = request.args.get('search', '')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute("""
            SELECT st.*, sec.section_name, u.username
            FROM students st
            JOIN sections sec ON st.section_id = sec.id
            JOIN users u ON st.user_id = u.id
            WHERE st.name LIKE %s OR st.roll_no LIKE %s
            ORDER BY sec.section_name, st.roll_no
        """, ('%' + search + '%', '%' + search + '%'))
    else:
        cursor.execute("""
            SELECT st.*, sec.section_name, u.username
            FROM students st
            JOIN sections sec ON st.section_id = sec.id
            JOIN users u ON st.user_id = u.id
            ORDER BY sec.section_name, st.roll_no
        """)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_all_students.html', students=students, search=search)

@app.route('/admin/view_student/<int:sid>')
def admin_view_student(sid):
    if not is_full_access():
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT st.*, sec.section_name, u.username
        FROM students st
        JOIN sections sec ON st.section_id = sec.id
        JOIN users u ON st.user_id = u.id
        WHERE st.id = %s
    """, (sid,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student not found!"

    cursor.execute("SELECT * FROM marks WHERE student_id = %s ORDER BY exam_date ASC", (sid,))
    marks = cursor.fetchall()

    cursor.execute("SELECT * FROM attendance WHERE student_id = %s ORDER BY date DESC", (sid,))
    attendance_records = cursor.fetchall()

    total_days   = len(attendance_records)
    present_days = sum(1 for a in attendance_records if a['status'] == 'Present')
    att_pct      = round((present_days / total_days * 100), 1) if total_days > 0 else 0

    cursor.execute("""
        SELECT a.title, a.subject, a.due_date, sa.status
        FROM student_assignments sa
        JOIN assignments a ON sa.assignment_id = a.id
        WHERE sa.student_id = %s ORDER BY a.due_date DESC
    """, (sid,))
    assignments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student_profile.html',
        student=student, marks=marks,
        attendance_records=attendance_records,
        att_pct=att_pct, assignments=assignments,
        total_days=total_days, present_days=present_days,
        from_admin=True
    )

@app.route('/admin/edit_student/<int:sid>', methods=['GET', 'POST'])
def admin_edit_student(sid):
    if not is_full_access():
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT st.*, u.username, u.password as user_password
        FROM students st JOIN users u ON st.user_id = u.id
        WHERE st.id = %s
    """, (sid,))
    student = cursor.fetchone()
    cursor.execute("SELECT * FROM sections")
    sections = cursor.fetchall()
    cursor.close()
    conn.close()

    if not student:
        return "Student not found!"

    msg = ''
    if request.method == 'POST':
        name         = request.form['name']
        roll_no      = request.form['roll_no']
        section_id   = request.form['section_id']
        username     = request.form['username']
        password     = request.form['password']
        email        = request.form.get('email', '')
        phone        = request.form.get('phone', '')
        dob          = request.form.get('dob') or None
        gender       = request.form.get('gender', '')
        parent_name  = request.form.get('parent_name', '')
        parent_phone = request.form.get('parent_phone', '')
        address      = request.form.get('address', '')

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id FROM students
                WHERE roll_no = %s AND section_id = %s AND id != %s
            """, (roll_no, section_id, sid))
            dup = cursor.fetchone()

            if dup:
                msg = 'Error: Another student with roll number ' + roll_no + ' already exists in this section!'
            else:
                cursor.execute("""
                    UPDATE students
                    SET name=%s, roll_no=%s, section_id=%s,
                        email=%s, phone=%s, dob=%s, gender=%s,
                        parent_name=%s, parent_phone=%s, address=%s
                    WHERE id=%s
                """, (name, roll_no, section_id, email, phone, dob, gender,
                      parent_name, parent_phone, address, sid))
                cursor.execute(
                    "UPDATE users SET full_name=%s, username=%s, password=%s WHERE id=%s",
                    (name, username, password, student['user_id'])
                )
                conn.commit()
                msg = 'SUCCESS: Student profile updated!'
                cursor.execute("""
                    SELECT st.*, u.username, u.password as user_password
                    FROM students st JOIN users u ON st.user_id = u.id
                    WHERE st.id = %s
                """, (sid,))
                student = cursor.fetchone()

            cursor.close()
            conn.close()
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('admin_edit_student.html',
        student=student, sections=sections, msg=msg
    )


@app.route('/admin/dedupe_students')
def admin_dedupe_students():
    if not is_full_access():
        return redirect(url_for('login'))

    removed = 0
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT roll_no, section_id, MIN(id) AS keep_id, COUNT(*) AS total
            FROM students
            GROUP BY roll_no, section_id
            HAVING COUNT(*) > 1
        """)
        dup_groups = cursor.fetchall()

        for grp in dup_groups:
            keep_id = grp['keep_id']
            cursor.execute("""
                SELECT id, user_id FROM students
                WHERE roll_no = %s AND section_id = %s AND id != %s
            """, (grp['roll_no'], grp['section_id'], keep_id))
            dupes = cursor.fetchall()

            for d in dupes:
                bad_id      = d['id']
                bad_user_id = d['user_id']

                cursor.execute("UPDATE marks SET student_id=%s WHERE student_id=%s", (keep_id, bad_id))
                cursor.execute("UPDATE attendance SET student_id=%s WHERE student_id=%s", (keep_id, bad_id))
                cursor.execute("""
                    UPDATE IGNORE student_assignments
                    SET student_id=%s WHERE student_id=%s
                """, (keep_id, bad_id))
                cursor.execute("DELETE FROM student_assignments WHERE student_id=%s", (bad_id,))

                cursor.execute("DELETE FROM students WHERE id=%s", (bad_id,))
                if bad_user_id:
                    cursor.execute("DELETE FROM users WHERE id=%s", (bad_user_id,))
                removed += 1

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return "Error while removing duplicates: " + str(e)

    return redirect(url_for('admin_all_students', dedupe_removed=removed))


@app.route('/admin/delete_student/<int:sid>')
def admin_delete_student(sid):
    if not is_full_access():
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM students WHERE id = %s", (sid,))
        row = cursor.fetchone()
        cursor.execute("DELETE FROM student_assignments WHERE student_id = %s", (sid,))
        cursor.execute("DELETE FROM marks WHERE student_id = %s", (sid,))
        cursor.execute("DELETE FROM attendance WHERE student_id = %s", (sid,))
        cursor.execute("DELETE FROM students WHERE id = %s", (sid,))
        if row:
            cursor.execute("DELETE FROM users WHERE id = %s", (row[0],))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    return redirect(url_for('admin_all_students'))

@app.route('/admin/marks')
def admin_all_marks():
    if not is_full_access():
        return redirect(url_for('login'))

    section_filter = request.args.get('section_id', '')
    subject_filter = request.args.get('subject', '')
    student_filter = request.args.get('student_id', '')
    exam_filter    = request.args.get('exam_name', '')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT m.*, st.name as student_name, st.roll_no, sec.section_name
        FROM marks m
        JOIN students st ON m.student_id = st.id
        JOIN sections sec ON st.section_id = sec.id
        WHERE 1=1
    """
    params = []
    if section_filter:
        query += " AND sec.id = %s"
        params.append(section_filter)
    if subject_filter:
        query += " AND m.subject = %s"
        params.append(subject_filter)
    if student_filter:
        query += " AND st.id = %s"
        params.append(student_filter)
    if exam_filter:
        query += " AND m.exam_name = %s"
        params.append(exam_filter)
    query += " ORDER BY m.exam_date DESC"

    cursor.execute(query, params)
    marks = cursor.fetchall()
    cursor.execute("SELECT * FROM sections")
    sections = cursor.fetchall()
    cursor.execute("SELECT * FROM subjects ORDER BY subject_name")
    subjects = cursor.fetchall()
    cursor.execute("""
        SELECT st.id, st.name, st.roll_no, sec.section_name
        FROM students st JOIN sections sec ON st.section_id = sec.id
        ORDER BY sec.section_name, st.roll_no
    """)
    students = cursor.fetchall()
    cursor.execute("SELECT DISTINCT exam_name FROM marks WHERE exam_name IS NOT NULL ORDER BY exam_name")
    exams = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin_all_marks.html',
        marks=marks, sections=sections, subjects=subjects,
        students=students, exams=exams,
        section_filter=section_filter, subject_filter=subject_filter,
        student_filter=student_filter, exam_filter=exam_filter
    )

@app.route('/admin/notices', methods=['GET', 'POST'])
def admin_notices():
    if not is_full_access():
        return redirect(url_for('login'))

    msg = ''
    if request.method == 'POST':
        title       = request.form['title']
        content     = request.form['content']
        target_role = request.form['target_role']
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO announcements (title, content, posted_by, target_role) VALUES (%s, %s, %s, %s)",
                (title, content, session['user_id'], target_role)
            )
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Announcement posted!'
        except Exception as e:
            msg = 'Error: ' + str(e)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, u.full_name as posted_by_name
        FROM announcements a
        JOIN users u ON a.posted_by = u.id
        ORDER BY a.created_at DESC
    """)
    notices = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_notices.html', notices=notices, msg=msg)


@app.route('/admin/delete_notice/<int:nid>')
def delete_notice(nid):
    if not is_full_access():
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM announcements WHERE id = %s", (nid,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_notices'))

@app.route('/admin/chart_data')
def admin_chart_data():
    if not is_full_access():
        return jsonify({'error': 'not allowed'})

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT sec.section_name, COUNT(st.id) as count
        FROM sections sec
        LEFT JOIN students st ON st.section_id = sec.id
        GROUP BY sec.id
    """)
    sec_rows = cursor.fetchall()

    cursor.execute("""
        SELECT subject, ROUND(AVG(marks_obtained/total_marks*100), 1) as avg_pct
        FROM marks
        WHERE total_marks > 0
        GROUP BY subject
    """)
    sub_rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            CASE
                WHEN gender = 'Male' THEN 'Boys'
                WHEN gender = 'Female' THEN 'Girls'
                ELSE 'Not specified'
            END as gender_label,
            COUNT(*) as count
        FROM students
        GROUP BY gender_label
        ORDER BY FIELD(gender_label, 'Boys', 'Girls', 'Not specified')
    """)
    gender_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'sec_labels': [r['section_name'] for r in sec_rows],
        'sec_data':   [r['count'] for r in sec_rows],
        'gender_labels': [r['gender_label'] for r in gender_rows],
        'gender_data':   [r['count'] for r in gender_rows],
        'sub_labels': [r['subject'] for r in sub_rows],
        'sub_data':   [float(r['avg_pct']) for r in sub_rows]
    })

@app.route('/teacher')
def teacher_dashboard():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    teacher_id = session['user_id']
    my_sections = get_teacher_sections(teacher_id)
    my_subjects = get_teacher_subjects(teacher_id)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (teacher_id,))
    teacher_info = cursor.fetchone()

    section_names = []
    if my_sections:
                                                              
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT section_name FROM sections WHERE id IN (" + placeholders + ")", my_sections)
        section_names = [r['section_name'] for r in cursor.fetchall()]

    student_count = 0
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE section_id IN (" + placeholders + ")", my_sections)
        student_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM assignments WHERE teacher_id = %s", (teacher_id,))
    assignment_count = cursor.fetchone()['cnt']

    recent_marks = []
    if my_sections and my_subjects:
        sec_ph = ','.join(['%s'] * len(my_sections))
        sub_ph = ','.join(['%s'] * len(my_subjects))
        cursor.execute("""
            SELECT m.*, st.name as student_name
            FROM marks m
            JOIN students st ON m.student_id = st.id
            WHERE st.section_id IN (""" + sec_ph + """)
              AND m.subject IN (""" + sub_ph + """)
            ORDER BY m.exam_date DESC LIMIT 5
        """, my_sections + my_subjects)
        recent_marks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('teacher_dashboard.html',
        teacher_info=teacher_info,
        student_count=student_count,
        assignment_count=assignment_count,
        recent_marks=recent_marks,
        section_names=section_names,
        my_subjects=my_subjects
    )

@app.route('/teacher/students')
def teacher_students():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])

    search = request.args.get('search', '')
    section_filter = request.args.get('section_id', '')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    sections = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + placeholders + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()

    students = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        query = """
            SELECT st.*, sec.section_name
            FROM students st
            JOIN sections sec ON st.section_id = sec.id
            WHERE st.section_id IN (""" + placeholders + """)
        """
        params = list(my_sections)
        if search:
            query += " AND (st.name LIKE %s OR st.roll_no LIKE %s)"
            params += ['%' + search + '%', '%' + search + '%']
        if section_filter and int(section_filter) in my_sections:
            query += " AND st.section_id = %s"
            params.append(section_filter)
        query += " ORDER BY sec.section_name, st.roll_no"

        cursor.execute(query, params)
        students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('teacher_students.html',
        students=students, sections=sections,
        search=search, section_filter=section_filter,
        my_sections=my_sections
    )


@app.route('/teacher/add_student', methods=['GET', 'POST'])
def add_student():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    sections = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + placeholders + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()
    cursor.close()
    conn.close()

    msg = ''
    if request.method == 'POST':
        name         = request.form['name']
        roll_no      = request.form['roll_no']
        section_id   = request.form['section_id']

        if int(section_id) not in my_sections:
            return render_template('add_student.html',
                sections=sections,
                msg='Error: You can only add students to sections you are assigned to.'
            )

        username     = request.form['username']
        password     = request.form['password']
        email        = request.form.get('email', '')
        phone        = request.form.get('phone', '')
        dob          = request.form.get('dob') or None
        gender       = request.form.get('gender', '')
        parent_name  = request.form.get('parent_name', '')
        parent_phone = request.form.get('parent_phone', '')
        address      = request.form.get('address', '')

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT id FROM students WHERE roll_no = %s AND section_id = %s",
                (roll_no, section_id)
            )
            dup = cursor.fetchone()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            dup_user = cursor.fetchone()

            if dup:
                cursor.close()
                conn.close()
                return render_template('add_student.html',
                    sections=sections,
                    msg='Error: A student with roll number ' + roll_no + ' already exists in this section!'
                )
            if dup_user:
                cursor.close()
                conn.close()
                return render_template('add_student.html',
                    sections=sections,
                    msg='Error: Username "' + username + '" is already taken. Please choose another.'
                )
                
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, 'student', %s)",
                (username, password, name)
            )
            new_user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO students
                (name, roll_no, section_id, user_id, email, phone, dob, gender,
                 parent_name, parent_phone, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, roll_no, section_id, new_user_id, email, phone, dob, gender,
                  parent_name, parent_phone, address))
            new_student_id = cursor.lastrowid
            conn.commit()

            cursor.execute("SELECT id FROM assignments WHERE section_id = %s", (section_id,))
            for a in cursor.fetchall():
                cursor.execute(
                    "INSERT INTO student_assignments (student_id, assignment_id) VALUES (%s, %s)",
                    (new_student_id, a[0])
                )
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Student added successfully!'
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('add_student.html', sections=sections, msg=msg)


@app.route('/teacher/edit_student/<int:sid>', methods=['GET', 'POST'])
def edit_student(sid):
    if not check_role('teacher'):
        return redirect(url_for('login'))
    my_sections = get_teacher_sections(session['user_id'])

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT st.*, u.username, u.password as user_password
        FROM students st JOIN users u ON st.user_id = u.id
        WHERE st.id = %s
    """, (sid,))
    student = cursor.fetchone()

                                                  
    sections = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + placeholders + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()
    cursor.close()
    conn.close()

    if not student:
        return "Student not found!"

                                                                          
    if student['section_id'] not in my_sections:
        return "Access denied: this student is not in one of your assigned sections."

    msg = ''
    if request.method == 'POST':
        name         = request.form['name']
        roll_no      = request.form['roll_no']
        section_id   = request.form['section_id']
        username     = request.form['username']
        password     = request.form['password']
        email        = request.form.get('email', '')
        phone        = request.form.get('phone', '')
        dob          = request.form.get('dob') or None
        gender       = request.form.get('gender', '')
        parent_name  = request.form.get('parent_name', '')
        parent_phone = request.form.get('parent_phone', '')
        address      = request.form.get('address', '')

                                                                              
        if int(section_id) not in my_sections:
            return render_template('edit_student.html',
                student=student, sections=sections,
                msg='Error: You cannot move this student to a section that is not assigned to you.'
            )

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

                                                                                         
            cursor.execute("""
                SELECT id FROM students
                WHERE roll_no = %s AND section_id = %s AND id != %s
            """, (roll_no, section_id, sid))
            dup = cursor.fetchone()

            if dup:
                msg = 'Error: Another student with roll number ' + roll_no + ' already exists in this section!'
            else:
                cursor.execute("""
                    UPDATE students
                    SET name=%s, roll_no=%s, section_id=%s,
                        email=%s, phone=%s, dob=%s, gender=%s,
                        parent_name=%s, parent_phone=%s, address=%s
                    WHERE id=%s
                """, (name, roll_no, section_id, email, phone, dob, gender,
                      parent_name, parent_phone, address, sid))
                cursor.execute(
                    "UPDATE users SET full_name=%s, username=%s, password=%s WHERE id=%s",
                    (name, username, password, student['user_id'])
                )
                conn.commit()
                msg = 'SUCCESS: Student updated!'

                                                                           
                cursor.execute("""
                    SELECT st.*, u.username, u.password as user_password
                    FROM students st JOIN users u ON st.user_id = u.id
                    WHERE st.id = %s
                """, (sid,))
                student = cursor.fetchone()

            cursor.close()
            conn.close()
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('edit_student.html', student=student, sections=sections, msg=msg)


@app.route('/teacher/delete_student/<int:sid>')
def delete_student(sid):
    if not check_role('teacher'):
        return redirect(url_for('login'))

                                                                
    my_sections = get_teacher_sections(session['user_id'])

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, section_id FROM students WHERE id = %s", (sid,))
        row = cursor.fetchone()
        if not row or row['section_id'] not in my_sections:
            cursor.close()
            conn.close()
            return "Access denied: this student is not in one of your sections."

        cursor.execute("DELETE FROM student_assignments WHERE student_id = %s", (sid,))
        cursor.execute("DELETE FROM marks WHERE student_id = %s", (sid,))
        cursor.execute("DELETE FROM attendance WHERE student_id = %s", (sid,))
        cursor.execute("DELETE FROM students WHERE id = %s", (sid,))
        if row['user_id']:
            cursor.execute("DELETE FROM users WHERE id = %s", (row['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    return redirect(url_for('teacher_students'))


@app.route('/teacher/student_profile/<int:sid>')
def student_profile(sid):
    if not check_role('teacher'):
        return redirect(url_for('login'))

                                                                 
    my_sections = get_teacher_sections(session['user_id'])

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT st.*, sec.section_name
        FROM students st JOIN sections sec ON st.section_id = sec.id
        WHERE st.id = %s
    """, (sid,))
    student = cursor.fetchone()

    if not student or student['section_id'] not in my_sections:
        cursor.close()
        conn.close()
        return "Access denied: this student is not in one of your sections."

                                                                 
    my_subjects = get_teacher_subjects(session['user_id'])
    marks = []
    if my_subjects:
        sub_ph = ','.join(['%s'] * len(my_subjects))
        cursor.execute("""
            SELECT * FROM marks
            WHERE student_id = %s AND subject IN (""" + sub_ph + """)
            ORDER BY exam_date ASC
        """, [sid] + my_subjects)
        marks = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM attendance WHERE student_id = %s ORDER BY date DESC
    """, (sid,))
    attendance_records = cursor.fetchall()

                                     
    total_days = len(attendance_records)
    present_days = sum(1 for a in attendance_records if a['status'] == 'Present')
    att_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0

    cursor.execute("""
        SELECT a.title, a.subject, a.due_date, sa.status
        FROM student_assignments sa
        JOIN assignments a ON sa.assignment_id = a.id
        WHERE sa.student_id = %s ORDER BY a.due_date DESC
    """, (sid,))
    assignments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student_profile.html',
        student=student,
        marks=marks,
        attendance_records=attendance_records,
        att_pct=att_pct,
        assignments=assignments,
        total_days=total_days,
        present_days=present_days
    )


                                                  
                                        
                                                  

@app.route('/teacher/assignments')
def teacher_assignments():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, sec.section_name,
               COUNT(sa.id) as total_students,
               SUM(CASE WHEN sa.status='Submitted' THEN 1 ELSE 0 END) as submitted_count
        FROM assignments a
        JOIN sections sec ON a.section_id = sec.id
        LEFT JOIN student_assignments sa ON a.id = sa.assignment_id
        WHERE a.teacher_id = %s
        GROUP BY a.id
        ORDER BY a.due_date DESC
    """, (teacher_id,))
    assignments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher_assignments.html', assignments=assignments)


@app.route('/teacher/add_assignment', methods=['GET', 'POST'])
def add_assignment():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    teacher_id  = session['user_id']
    my_sections = get_teacher_sections(teacher_id)
    my_subjects = get_teacher_subjects(teacher_id)

                                                
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    sections = []
    subjects = []
    if my_sections:
        sec_ph = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + sec_ph + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()
    if my_subjects:
        sub_ph = ','.join(['%s'] * len(my_subjects))
        cursor.execute("SELECT * FROM subjects WHERE subject_name IN (" + sub_ph + ") ORDER BY subject_name", my_subjects)
        subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    msg = ''
    if request.method == 'POST':
        title       = request.form['title']
        description = request.form['description']
        subject     = request.form['subject']
        due_date    = request.form['due_date']
        section_id  = request.form['section_id']

                                        
        if int(section_id) not in my_sections or subject not in my_subjects:
            return render_template('add_assignment.html',
                sections=sections, subjects=subjects,
                msg='Error: You can only create assignments for your own sections and subjects.'
            )

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO assignments (title, description, subject, due_date, section_id, teacher_id) VALUES (%s,%s,%s,%s,%s,%s)",
                (title, description, subject, due_date, section_id, teacher_id)
            )
            new_id = cursor.lastrowid
            conn.commit()

                                                    
            cursor.execute("SELECT id FROM students WHERE section_id = %s", (section_id,))
            for s in cursor.fetchall():
                cursor.execute(
                    "INSERT INTO student_assignments (student_id, assignment_id) VALUES (%s, %s)",
                    (s[0], new_id)
                )
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Assignment created and assigned to section!'
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('add_assignment.html', sections=sections, subjects=subjects, msg=msg)


@app.route('/teacher/edit_assignment/<int:aid>', methods=['GET', 'POST'])
def edit_assignment(aid):
    if not check_role('teacher'):
        return redirect(url_for('login'))

    teacher_id  = session['user_id']
    my_subjects = get_teacher_subjects(teacher_id)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM assignments WHERE id = %s AND teacher_id = %s", (aid, teacher_id))
    assignment = cursor.fetchone()
    cursor.execute("SELECT * FROM sections")
    sections = cursor.fetchall()
                                                     
    subjects = [{'subject_name': s} for s in my_subjects]
    cursor.close()
    conn.close()

    if not assignment:
        return "Assignment not found or you do not have access to it!"

    msg = ''
    if request.method == 'POST':
        title       = request.form['title']
        description = request.form['description']
        subject     = request.form['subject']
        due_date    = request.form['due_date']

        if subject not in my_subjects:
            msg = 'Error: You can only assign subjects you teach.'
            return render_template('edit_assignment.html',
                assignment=assignment, sections=sections, subjects=subjects, msg=msg)

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE assignments SET title=%s, description=%s, subject=%s, due_date=%s WHERE id=%s AND teacher_id=%s",
                (title, description, subject, due_date, aid, teacher_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Assignment updated!'
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('edit_assignment.html', assignment=assignment, sections=sections, subjects=subjects, msg=msg)


@app.route('/teacher/delete_assignment/<int:aid>')
def delete_assignment(aid):
    if not check_role('teacher'):
        return redirect(url_for('login'))
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_assignments WHERE assignment_id = %s", (aid,))
        cursor.execute("DELETE FROM assignments WHERE id = %s AND teacher_id = %s", (aid, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    return redirect(url_for('teacher_assignments'))


                                                  
                                   
                                                  

@app.route('/teacher/marks')
def teacher_marks():
    if not check_role('teacher'):
        return redirect(url_for('login'))

                                                                      
    my_sections = get_teacher_sections(session['user_id'])
    my_subjects = get_teacher_subjects(session['user_id'])

                                            
    if not my_sections or not my_subjects:
        return render_template('teacher_marks.html',
            marks=[], sections=[], subjects=[], students=[], exams=[],
            section_filter='', subject_filter='', student_filter='', exam_filter='',
            unassigned=True
        )

                                                                            
    section_filter = request.args.get('section_id', '')
    subject_filter = request.args.get('subject', '')
    student_filter = request.args.get('student_id', '')
    exam_filter    = request.args.get('exam_name', '')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

                                                                            
    sec_ph = ','.join(['%s'] * len(my_sections))
    sub_ph = ','.join(['%s'] * len(my_subjects))
    cursor.execute("SELECT * FROM sections WHERE id IN (" + sec_ph + ") ORDER BY section_name", my_sections)
    sections = cursor.fetchall()
    cursor.execute("SELECT * FROM subjects WHERE subject_name IN (" + sub_ph + ") ORDER BY subject_name", my_subjects)
    subjects = cursor.fetchall()
    cursor.execute("""
        SELECT st.id, st.name, st.roll_no, sec.section_name
        FROM students st JOIN sections sec ON st.section_id = sec.id
        WHERE st.section_id IN (""" + sec_ph + """)
        ORDER BY sec.section_name, st.roll_no
    """, my_sections)
    students = cursor.fetchall()
    cursor.execute("SELECT DISTINCT exam_name FROM marks WHERE exam_name IS NOT NULL ORDER BY exam_name")
    exams = cursor.fetchall()

                                                              
    query = """
        SELECT m.*, st.name as student_name, st.roll_no, sec.section_name
        FROM marks m
        JOIN students st ON m.student_id = st.id
        JOIN sections sec ON st.section_id = sec.id
        WHERE sec.id IN (""" + sec_ph + """)
          AND m.subject IN (""" + sub_ph + """)
    """
    params = list(my_sections) + list(my_subjects)

    if section_filter and int(section_filter) in my_sections:
        query += " AND sec.id = %s"
        params.append(section_filter)
    if subject_filter and subject_filter in my_subjects:
        query += " AND m.subject = %s"
        params.append(subject_filter)
    if student_filter:
        query += " AND st.id = %s"
        params.append(student_filter)
    if exam_filter:
        query += " AND m.exam_name = %s"
        params.append(exam_filter)
    query += " ORDER BY m.exam_date DESC"

    cursor.execute(query, params)
    marks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher_marks.html',
        marks=marks, sections=sections, subjects=subjects,
        students=students, exams=exams,
        section_filter=section_filter, subject_filter=subject_filter,
        student_filter=student_filter, exam_filter=exam_filter,
        unassigned=False
    )


@app.route('/teacher/enter_marks', methods=['GET', 'POST'])
def enter_marks():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])
    my_subjects = get_teacher_subjects(session['user_id'])

                                                                  
    students = []
    subjects = []
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if my_sections:
        sec_ph = ','.join(['%s'] * len(my_sections))
        cursor.execute("""
            SELECT st.*, sec.section_name FROM students st
            JOIN sections sec ON st.section_id = sec.id
            WHERE st.section_id IN (""" + sec_ph + """)
            ORDER BY sec.section_name, st.roll_no
        """, my_sections)
        students = cursor.fetchall()
    if my_subjects:
        sub_ph = ','.join(['%s'] * len(my_subjects))
        cursor.execute("SELECT * FROM subjects WHERE subject_name IN (" + sub_ph + ") ORDER BY subject_name", my_subjects)
        subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    msg = ''
    if request.method == 'POST':
        student_id     = request.form['student_id']
        subject        = request.form['subject']
        exam_name      = request.form['exam_name']
        marks_obtained = request.form['marks_obtained']
        total_marks    = request.form['total_marks']
        exam_date      = request.form['exam_date']

                                                                                                     
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT section_id FROM students WHERE id=%s", (student_id,))
            row = cursor.fetchone()
            if not row or row['section_id'] not in my_sections:
                cursor.close()
                conn.close()
                return render_template('enter_marks.html',
                    students=students, subjects=subjects,
                    msg='Error: You cannot enter marks for a student outside your sections.'
                )
            if subject not in my_subjects:
                cursor.close()
                conn.close()
                return render_template('enter_marks.html',
                    students=students, subjects=subjects,
                    msg='Error: You cannot enter marks for a subject you are not assigned to teach.'
                )

            cursor.execute(
                "INSERT INTO marks (student_id, subject, exam_name, marks_obtained, total_marks, exam_date) VALUES (%s,%s,%s,%s,%s,%s)",
                (student_id, subject, exam_name, marks_obtained, total_marks, exam_date)
            )
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Marks saved!'
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('enter_marks.html', students=students, subjects=subjects, msg=msg)


@app.route('/teacher/edit_marks/<int:mid>', methods=['GET', 'POST'])
def edit_marks(mid):
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])
    my_subjects = get_teacher_subjects(session['user_id'])

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
                                                                                   
    cursor.execute("""
        SELECT m.*, st.section_id AS stu_section
        FROM marks m JOIN students st ON m.student_id = st.id
        WHERE m.id = %s
    """, (mid,))
    mark = cursor.fetchone()

    if not mark:
        cursor.close()
        conn.close()
        return "Marks record not found!"

                                                                    
    if mark['stu_section'] not in my_sections or mark['subject'] not in my_subjects:
        cursor.close()
        conn.close()
        return "Access denied: this marks record is outside your assigned scope."

                                 
    students = []
    subjects = []
    if my_sections:
        sec_ph = ','.join(['%s'] * len(my_sections))
        cursor.execute("""
            SELECT st.*, sec.section_name FROM students st
            JOIN sections sec ON st.section_id = sec.id
            WHERE st.section_id IN (""" + sec_ph + """)
            ORDER BY sec.section_name, st.roll_no
        """, my_sections)
        students = cursor.fetchall()
    if my_subjects:
        sub_ph = ','.join(['%s'] * len(my_subjects))
        cursor.execute("SELECT * FROM subjects WHERE subject_name IN (" + sub_ph + ") ORDER BY subject_name", my_subjects)
        subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    msg = ''
    if request.method == 'POST':
        subject        = request.form['subject']
        exam_name      = request.form['exam_name']
        marks_obtained = request.form['marks_obtained']
        total_marks    = request.form['total_marks']
        exam_date      = request.form['exam_date']

                                                                         
        if subject not in my_subjects:
            msg = 'Error: You cannot change the subject to one you are not assigned to teach.'
        else:
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE marks SET subject=%s, exam_name=%s, marks_obtained=%s, total_marks=%s, exam_date=%s WHERE id=%s",
                    (subject, exam_name, marks_obtained, total_marks, exam_date, mid)
                )
                conn.commit()
                cursor.close()
                conn.close()
                msg = 'SUCCESS: Marks updated!'
            except Exception as e:
                msg = 'Error: ' + str(e)

    return render_template('edit_marks.html', mark=mark, students=students, subjects=subjects, msg=msg)


@app.route('/teacher/delete_marks/<int:mid>')
def delete_marks(mid):
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])
    my_subjects = get_teacher_subjects(session['user_id'])

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
                                                                    
        cursor.execute("""
            SELECT m.subject, st.section_id
            FROM marks m JOIN students st ON m.student_id = st.id
            WHERE m.id = %s
        """, (mid,))
        row = cursor.fetchone()
        if row and row['section_id'] in my_sections and row['subject'] in my_subjects:
            cursor.execute("DELETE FROM marks WHERE id = %s", (mid,))
            conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    return redirect(url_for('teacher_marks'))


                                                  
                      
                                                  

@app.route('/teacher/attendance', methods=['GET', 'POST'])
def teacher_attendance():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])

    msg = ''
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
                                                  
    sections = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + placeholders + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()
    cursor.close()
    conn.close()

                                   
    selected_section = request.args.get('section_id', '')
    selected_date    = request.args.get('date', '')
    students = []

                                                                           
    if selected_section and selected_date and int(selected_section) in my_sections:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT st.*, sec.section_name,
                   COALESCE(a.status, 'Present') as att_status
            FROM students st
            JOIN sections sec ON st.section_id = sec.id
            LEFT JOIN attendance a ON a.student_id = st.id AND a.date = %s
            WHERE st.section_id = %s
            ORDER BY st.roll_no
        """, (selected_date, selected_section))
        students = cursor.fetchall()
        cursor.close()
        conn.close()

    if request.method == 'POST':
        att_date   = request.form['att_date']
        sec_id     = request.form['section_id']

                                                                     
        if int(sec_id) not in my_sections:
            return render_template('teacher_attendance.html',
                sections=sections, students=[],
                selected_section=selected_section, selected_date=selected_date,
                msg='Error: You cannot mark attendance for a section that is not assigned to you.'
            )
                                                                  

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM students WHERE section_id = %s", (sec_id,))
            all_students = cursor.fetchall()

            for s in all_students:
                stud_id   = s['id']
                status_key = 'status_' + str(stud_id)
                status    = request.form.get(status_key, 'Present')

                                                                  
                cursor.execute(
                    "SELECT id FROM attendance WHERE student_id=%s AND date=%s",
                    (stud_id, att_date)
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE attendance SET status=%s WHERE student_id=%s AND date=%s",
                        (status, stud_id, att_date)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
                        (stud_id, att_date, status)
                    )
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'SUCCESS: Attendance saved for ' + att_date
        except Exception as e:
            msg = 'Error: ' + str(e)

    return render_template('teacher_attendance.html',
        sections=sections,
        students=students,
        selected_section=selected_section,
        selected_date=selected_date,
        msg=msg
    )


@app.route('/teacher/view_attendance')
def view_attendance():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])
    section_filter = request.args.get('section_id', '')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    sections = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + placeholders + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()

    records = []
    if section_filter and int(section_filter) in my_sections:
        cursor.execute("""
            SELECT a.*, st.name as student_name, st.roll_no, sec.section_name
            FROM attendance a
            JOIN students st ON a.student_id = st.id
            JOIN sections sec ON st.section_id = sec.id
            WHERE sec.id = %s
            ORDER BY a.date DESC, st.roll_no
        """, (section_filter,))
        records = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('view_attendance.html', sections=sections, records=records, section_filter=section_filter)


                                                  
                                             
                                                  

@app.route('/teacher/section_charts')
def section_charts():
    if not check_role('teacher'):
        return redirect(url_for('login'))

    my_sections = get_teacher_sections(session['user_id'])
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    sections = []
    if my_sections:
        placeholders = ','.join(['%s'] * len(my_sections))
        cursor.execute("SELECT * FROM sections WHERE id IN (" + placeholders + ") ORDER BY section_name", my_sections)
        sections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('section_charts.html', sections=sections)


@app.route('/teacher/section_chart_data')
def section_chart_data():
    if not check_role('teacher'):
        return jsonify({'error': 'not allowed'})

    my_sections = get_teacher_sections(session['user_id'])

    section_id = request.args.get('section_id', '')
    if not section_id:
        return jsonify({'error': 'no section selected'})

                                                                         
    if int(section_id) not in my_sections:
        return jsonify({'error': 'access denied'})

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

                                           
    cursor.execute("""
        SELECT m.subject,
               ROUND(AVG(m.marks_obtained / m.total_marks * 100), 1) as avg_pct
        FROM marks m
        JOIN students st ON m.student_id = st.id
        WHERE st.section_id = %s AND m.total_marks > 0
        GROUP BY m.subject
    """, (section_id,))
    sub_rows = cursor.fetchall()

                                                       
    cursor.execute("""
        SELECT st.name,
               ROUND(AVG(m.marks_obtained / m.total_marks * 100), 1) as avg_pct
        FROM marks m
        JOIN students st ON m.student_id = st.id
        WHERE st.section_id = %s AND m.total_marks > 0
        GROUP BY st.id
        ORDER BY avg_pct DESC
    """, (section_id,))
    stud_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'sub_labels':  [r['subject'] for r in sub_rows],
        'sub_data':    [float(r['avg_pct']) for r in sub_rows],
        'stud_labels': [r['name'] for r in stud_rows],
        'stud_data':   [float(r['avg_pct']) for r in stud_rows]
    })


                                                  
                     
                                                  

@app.route('/student')
def student_dashboard():
    if not check_role('student'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT st.*, sec.section_name
        FROM students st JOIN sections sec ON st.section_id = sec.id
        WHERE st.user_id = %s
    """, (user_id,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return "Student record not found. Please contact your teacher."

    student_id = student['id']

                                 
    cursor.execute("""
        SELECT a.id as assignment_id, a.title, a.subject, a.due_date, a.description, sa.status
        FROM student_assignments sa
        JOIN assignments a ON sa.assignment_id = a.id
        WHERE sa.student_id = %s
        ORDER BY a.due_date DESC
    """, (student_id,))
    assignments = cursor.fetchall()

                                           
    cursor.execute("""
        SELECT * FROM marks WHERE student_id = %s ORDER BY exam_date DESC
    """, (student_id,))
    raw_marks = cursor.fetchall()
    marks = []
    for m in raw_marks:
        pct = round((m['marks_obtained'] / m['total_marks']) * 100, 1) if m['total_marks'] > 0 else 0
        marks.append({**m, 'percent': pct})

                            
    cursor.execute("SELECT status, COUNT(*) as cnt FROM attendance WHERE student_id=%s GROUP BY status", (student_id,))
    att_rows = cursor.fetchall()
    att_summary = {r['status']: r['cnt'] for r in att_rows}
    total_days   = sum(att_summary.values())
    present_days = att_summary.get('Present', 0)
    att_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0

                                             
    cursor.execute("""
        SELECT a.*, u.full_name as posted_by_name
        FROM announcements a
        JOIN users u ON a.posted_by = u.id
        WHERE a.target_role IN ('all', 'student')
        ORDER BY a.created_at DESC LIMIT 5
    """)
    notices = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student_dashboard.html',
        student=student,
        assignments=assignments,
        marks=marks,
        att_pct=att_pct,
        present_days=present_days,
        total_days=total_days,
        notices=notices
    )


                                                  
                             
                                                  

@app.route('/student/chart_data')
def student_chart_data():
    if not check_role('student'):
        return jsonify({'error': 'Not logged in'})

    filter_type = request.args.get('filter', 'all')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()
    if not student:
        return jsonify({'error': 'Student not found'})

    cursor.execute("""
        SELECT subject, exam_name, marks_obtained, total_marks, exam_date
        FROM marks WHERE student_id = %s ORDER BY exam_date ASC
    """, (student['id'],))
    all_marks = cursor.fetchall()
    cursor.close()
    conn.close()

    if filter_type == 'last5':
        all_marks = all_marks[-10:]

                                         
    line_labels = [m['exam_name'] + ' (' + m['subject'][:3] + ')' for m in all_marks]
    line_data   = [round(m['marks_obtained'] / m['total_marks'] * 100, 1) if m['total_marks'] > 0 else 0 for m in all_marks]

                                     
    subj_map = {}
    for m in all_marks:
        s = m['subject']
        if s not in subj_map:
            subj_map[s] = [0, 0]
        subj_map[s][0] += m['marks_obtained']
        subj_map[s][1] += m['total_marks']

    bar_labels = list(subj_map.keys())
    bar_data   = [round(subj_map[s][0] / subj_map[s][1] * 100, 1) if subj_map[s][1] > 0 else 0 for s in bar_labels]

    return jsonify({'line_labels': line_labels, 'line_data': line_data, 'bar_labels': bar_labels, 'bar_data': bar_data})


                                                  
                             
                                                  

@app.route('/student/submit/<int:assignment_id>')
def submit_assignment(assignment_id):
    if not check_role('student'):
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
    student = cursor.fetchone()
    if student:
        cursor.execute(
            "UPDATE student_assignments SET status='Submitted' WHERE student_id=%s AND assignment_id=%s",
            (student['id'], assignment_id)
        )
        conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('student_dashboard'))


                                                  
                                
                                                  

@app.route('/student/attendance')
def student_attendance():
    if not check_role('student'):
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
    student = cursor.fetchone()

    records = []
    if student:
        cursor.execute("SELECT * FROM attendance WHERE student_id=%s ORDER BY date DESC", (student['id'],))
        records = cursor.fetchall()

                     
    total = len(records)
    present = sum(1 for r in records if r['status'] == 'Present')
    absent  = sum(1 for r in records if r['status'] == 'Absent')
    late    = sum(1 for r in records if r['status'] == 'Late')
    pct = round((present / total * 100), 1) if total > 0 else 0

    cursor.close()
    conn.close()
    return render_template('student_attendance.html',
        records=records, total=total,
        present=present, absent=absent, late=late, pct=pct
    )


                                                  
                            
                                                  

@app.route('/student/notices')
def student_notices():
    if not check_role('student'):
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, u.full_name as posted_by_name
        FROM announcements a
        JOIN users u ON a.posted_by = u.id
        WHERE a.target_role IN ('all', 'student')
        ORDER BY a.created_at DESC
    """)
    notices = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('student_notices.html', notices=notices)


                                                  
                           
                                                  

@app.route('/student/change_password', methods=['GET', 'POST'])
def change_password():
    if not check_role('student'):
        return redirect(url_for('login'))

    msg = ''
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm      = request.form['confirm_password']

        if new_password != confirm:
            msg = 'Error: New passwords do not match!'
        else:
            try:
                conn = get_db()
                cursor = conn.cursor(dictionary=True)
                                                  
                cursor.execute("SELECT * FROM users WHERE id=%s AND password=%s", (session['user_id'], old_password))
                user = cursor.fetchone()
                if not user:
                    msg = 'Error: Old password is incorrect!'
                else:
                    cursor.execute("UPDATE users SET password=%s WHERE id=%s", (new_password, session['user_id']))
                    conn.commit()
                    msg = 'SUCCESS: Password changed successfully!'
                cursor.close()
                conn.close()
            except Exception as e:
                msg = 'Error: ' + str(e)

    return render_template('change_password.html', msg=msg)


                                                 
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
