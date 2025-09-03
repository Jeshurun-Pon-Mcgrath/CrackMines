from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
import mysql.connector, re, random, os

app = Flask(__name__)
app.secret_key = 'replace_with_a_secure_random_secret'

# ✅ TiDB Cloud DB Connection Function
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=4000,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_ca="isrgrootx1.pem",   # CA cert you must include in your project folder
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )

# ✅ Flask-Mail config (use Gmail app password)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'crackmines34@gmail.com'
app.config['MAIL_PASSWORD'] = 'xjll wtxs kzjd tkxy'  # Gmail App password

mail = Mail(app)

def user_by_email(email):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    account = cur.fetchone()
    db.close()
    return account

def ensure_login():
    return 'loggedin' in session

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
                session['loggedin'] = True
                session['id'] = account['id']
                session['name'] = account['name']
                session['email'] = account['email']
                session['role'] = 'teacher'
                db.close()
                return redirect(url_for('dashboard'))
            else:
                otp = str(random.randint(100000, 999999))
                cur.execute("UPDATE users SET otp=%s WHERE id=%s", (otp, account['id']))
                db.commit()
                try:
                    m = Message('CrackMines Login OTP', sender=app.config['MAIL_USERNAME'], recipients=[email])
                    m.body = f"Your OTP is {otp}. It is valid for 10 minutes."
                    mail.send(m)
                except Exception as e:
                    print("MAIL ERROR:", e)
                db.close()
                return redirect(url_for('verify_otp_login', email=email))
        db.close()
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
                cur.execute("INSERT INTO users(name,email,password,role,otp) VALUES(%s,%s,%s,%s,%s)", (name,email,password,role,otp))
                db.commit()
                try:
                    m = Message('CrackMines OTP', sender=app.config['MAIL_USERNAME'], recipients=[email])
                    m.body = f"Welcome {name}! Your OTP is {otp}."
                    mail.send(m)
                except Exception as e:
                    print("MAIL ERROR:", e)
                db.close()
                return redirect(url_for('verify_otp', email=email))
            else:
                cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)", (name,email,password,role))
                db.commit()
                db.close()
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
            db.close()
            flash("OTP verified. Please login.")
            return redirect(url_for('login'))
        db.close()
        msg = "Wrong OTP"
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
            session['loggedin'] = True
            session['id'] = acc['id']
            session['name'] = acc['name']
            session['email'] = acc['email']
            session['role'] = acc['role']
            db.close()
            return redirect(url_for('dashboard'))
        db.close()
        msg = "Wrong OTP"
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

@app.route('/createquiz')
def createquiz():
    if not ensure_login(): return redirect(url_for('login'))
    if session.get('role') != 'teacher':
        flash("Only teachers can create quizzes.")
        return redirect(url_for('dashboard'))
    return render_template('createquiz.html')

@app.route('/livequiz')
def livequiz():
    if not ensure_login(): return redirect(url_for('login'))
    return render_template('livequiz.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('front'))

@app.route('/api/leaderboard')
def api_leaderboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT u.name, MAX(s.score) AS score
        FROM scores s
        JOIN users u ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY score DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    db.close()
    return jsonify(rows)

@app.route('/api/stats')
def api_stats():
    if not ensure_login(): return jsonify({'error':'not logged in'}), 401
    uid = session['id']
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as taken, COALESCE(AVG(score),0) as avg_score, COALESCE(MAX(score),0) as best FROM scores WHERE user_id=%s", (uid,))
    row = cur.fetchone()
    db.close()
    return jsonify(row)

@app.route('/api/quizzes', methods=['POST'])
def api_create_quiz():
    if not ensure_login() or session.get('role') != 'teacher':
        return jsonify({'ok': False, 'error':'Not allowed'}), 403
    data = request.get_json()
    title = data.get('title')
    questions = data.get('questions', [])
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("INSERT INTO quizzes(title, teacher_id) VALUES(%s,%s)", (title, session['id']))
    db.commit()
    quiz_id = cur.lastrowid
    for q in questions:
        cur.execute("""
            INSERT INTO questions(quiz_id,question_text,option_a,option_b,option_c,option_d,correct_answer)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (quiz_id, q['text'], q['A'], q['B'], q['C'], q['D'], q['correct']))
    db.commit()
    db.close()
    return jsonify({'ok': True, 'quiz_id': quiz_id})

if __name__ == "__main__":
    app.run(debug=True)
