from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
import mysql.connector
import re, random, os

from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "replace_with_secure_key")

# Database connection
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),   # ✅ Added this
        database=os.getenv("DB_NAME"),
        ssl_ca=os.getenv("DB_SSL_CA"),
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )


# ✅ Mail config (with your password)
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", "587"))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "crackmines34@gmail.com")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "xjll wtxs kzjd tkxy")

mail = Mail(app)

# -------------------- Helpers --------------------
def user_by_email(email):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    db.close()
    return user

def ensure_login():
    return 'loggedin' in session

# -------------------- Routes --------------------
@app.route('/')
def front():
    return render_template('Frontpg.html')

@app.route('/login', methods=['GET','POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email,password))
        account = cur.fetchone()
        if not account:
            msg = "Invalid credentials"
        else:
            if account['role'] == 'teacher':
                session.update({
                    'loggedin': True,
                    'id': account['id'],
                    'name': account['name'],
                    'email': account['email'],
                    'role': 'teacher'
                })
                cur.close(); db.close()
                return redirect(url_for('dashboard'))
            else:
                otp = str(random.randint(100000, 999999))
                cur.execute("UPDATE users SET otp=%s WHERE id=%s", (otp, account['id']))
                db.commit()
                try:
                    m = Message('CrackMines Login OTP',
                                sender=app.config['MAIL_USERNAME'],
                                recipients=[email])
                    m.body = f"Your OTP is {otp}. It is valid for 10 minutes."
                    mail.send(m)
                except Exception as e:
                    print("MAIL ERROR:", e)
                cur.close(); db.close()
                return redirect(url_for('verify_otp_login', email=email))
        cur.close(); db.close()
    return render_template('login.html', msg=msg)

@app.route('/signup', methods=['GET','POST'])
def signup():
    msg = ''
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = "Invalid email"
        elif user_by_email(email):
            msg = "Account already exists"
        else:
            domain = email.split('@')[-1]
            role = 'teacher' if domain == 'karunya.edu' else 'student'
            db = get_db()
            cur = db.cursor(dictionary=True)

            if role == 'student':
                otp = str(random.randint(100000,999999))
                cur.execute(
                    "INSERT INTO users(name,email,password,role,otp) VALUES(%s,%s,%s,%s,%s)",
                    (name,email,password,role,otp)
                )
                db.commit()
                try:
                    m = Message('CrackMines OTP',
                                sender=app.config['MAIL_USERNAME'],
                                recipients=[email])
                    m.body = f"Welcome {name}! Your OTP is {otp}."
                    mail.send(m)
                except Exception as e:
                    print("MAIL ERROR:", e)
                cur.close(); db.close()
                return redirect(url_for('verify_otp', email=email))
            else:
                cur.execute(
                    "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
                    (name,email,password,role)
                )
                db.commit()
                cur.close(); db.close()
                flash("Teacher account created. Please login.")
                return redirect(url_for('login'))
    return render_template('signup.html', msg=msg)

@app.route('/verify_otp/<email>', methods=['GET','POST'])
def verify_otp(email):
    msg = ''
    if request.method == 'POST':
        otp = request.form['otp']
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND otp=%s", (email, otp))
        acc = cur.fetchone()
        if acc:
            cur.execute("UPDATE users SET otp=NULL WHERE id=%s", (acc['id'],))
            db.commit()
            flash("OTP verified. Please login.")
            cur.close(); db.close()
            return redirect(url_for('login'))
        msg = "Wrong OTP"
        cur.close(); db.close()
    return render_template('verify_otp.html', email=email, msg=msg)

@app.route('/verify_otp_login/<email>', methods=['GET','POST'])
def verify_otp_login(email):
    msg = ''
    if request.method == 'POST':
        otp = request.form['otp']
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND otp=%s", (email, otp))
        acc = cur.fetchone()
        if acc:
            cur.execute("UPDATE users SET otp=NULL WHERE id=%s", (acc['id'],))
            db.commit()
            session.update({
                'loggedin': True,
                'id': acc['id'],
                'name': acc['name'],
                'email': acc['email'],
                'role': acc['role']
            })
            cur.close(); db.close()
            return redirect(url_for('dashboard'))
        msg = "Wrong OTP"
        cur.close(); db.close()
    return render_template('verify_otp.html', email=email, msg=msg)

@app.route('/dashboard')
def dashboard():
    if not ensure_login(): return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/stats')
def stats():
    if not ensure_login(): return redirect(url_for('login'))
    return render_template('stats.html')

@app.route('/profile')
def profile():
    if not ensure_login(): return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/leaderboard')
def leaderboard():
    if not ensure_login(): return redirect(url_for('login'))
    return render_template('leaderboard.html')

"""@app.route('/createquiz')
def createquiz():
    if not ensure_login(): return redirect(url_for('login'))
    if session.get('role') != 'teacher':
        flash("Only teachers can create quizzes.")
        return redirect(url_for('dashboard'))
    return render_template('createquiz.html')

@app.route('/livequiz')
def livequiz():
    if not ensure_login(): return redirect(url_for('login'))
    return render_template('livequiz.html')"""

@app.route('/createquiz', methods=['GET','POST'])
def createquiz():
    if not ensure_login(): return redirect(url_for('login'))
    if session.get('role') != 'teacher':
        flash("Only teachers can create quizzes.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        teacher_id = session['id']
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO quizzes (title, teacher_id) VALUES (%s, %s)", (title, teacher_id))
        quiz_id = cur.lastrowid

        # Save questions
        questions = request.form.getlist('question')
        options_a = request.form.getlist('option_a')
        options_b = request.form.getlist('option_b')
        options_c = request.form.getlist('option_c')
        options_d = request.form.getlist('option_d')
        answers = request.form.getlist('answer')

        for i in range(len(questions)):
            cur.execute("""
                INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (quiz_id, questions[i], options_a[i], options_b[i], options_c[i], options_d[i], answers[i]))

        db.commit()
        cur.close(); db.close()
        flash("Quiz created successfully!")
        return redirect(url_for('dashboard'))

    return render_template('createquiz.html')


@app.route('/livequiz/<int:quiz_id>', methods=['GET','POST'])
def livequiz(quiz_id):
    if not ensure_login(): return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM questions WHERE quiz_id=%s", (quiz_id,))
    questions = cur.fetchall()

    if request.method == 'POST':
        score = 0
        for q in questions:
            ans = request.form.get(str(q['id']))
            if ans == q['correct_answer']:
                score += 1
        cur.execute("INSERT INTO scores (user_id, quiz_id, score) VALUES (%s,%s,%s)",
                    (session['id'], quiz_id, score))
        db.commit()
        cur.close(); db.close()
        flash(f"You scored {score}/{len(questions)}")
        return redirect(url_for('dashboard'))

    cur.close(); db.close()
    return render_template('livequiz.html', questions=questions)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('front'))
