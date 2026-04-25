# app.py
# Student Assignment Tracker and Performance Analyzer
# Made by: Shlok Vaidya

from flask import Flask, session, request, redirect, url_for, render_template, send_from_directory
import os
import mysql.connector
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

PUBLIC_DIR = os.path.join(app.root_path, 'public')

# Helper: Database Connection
def get_db():
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    return conn

# Helper: Check if user is logged in with correct role
def check_role(role):
    if 'user_id' not in session:
        return False
    if session["role"] != role:
        return False
    return True

#Helper: LOGIN / LOGOUT
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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(PUBLIC_DIR, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/public/<path:filename>')
def public_file(filename):
    return send_from_directory(PUBLIC_DIR, filename)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session['role']
    # admin / vice principle / coordinator land on the admin dashboard
    if role in ('admin', 'vice_principal', 'coordinator'):
        return render_template('admin_dashboard.html')
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Helper: is the logged-in user allowed to see ALL student records ?
# Only Admin, Vice Principle, Coordinator have access to full-records
def is_full_access():
    if 'user_id' not in session:
        return False
    return session.get('role') in ('admin', 'vice_principal', 'coordinator')
 
#Helper: Can this user open teacher-style pages ?
def check_teacher_access():
    if 'user_id' not in session:
        return False
    return session.get('role') in ('teacher', 'admin', 'vice_principal', 'coordinator')

# Running
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
