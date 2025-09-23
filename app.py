# app.py - PhenBOT Complete Flask Application

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import traceback
from datetime import datetime
import PyPDF2

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

DATABASE = 'phenbot.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# -------------------- Database --------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        mode TEXT,
        length_preference TEXT,
        question TEXT,
        answer TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        original_filename TEXT,
        file_path TEXT,
        file_type TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        front TEXT,
        back TEXT,
        subject TEXT,
        difficulty TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    conn.commit()
    conn.close()

init_db()

# -------------------- Helpers --------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception as e:
        print("PDF extraction error:", e)
        return None

def get_user(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    try:
        pw_hash = generate_password_hash(password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# -------------------- HTML Templates --------------------
LOGIN_HTML = """ ... (your login HTML unchanged) ... """
REGISTER_HTML = """ ... (your register HTML unchanged) ... """
MAIN_APP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PhenBOT Dashboard</title>
  <style>
    /* keep all your CSS here */
  </style>
</head>
<body>
  <div class="header">
    <div class="header-content">
      <div class="logo">🤖 PhenBOT</div>
      <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
    </div>
  </div>

  <div class="main-container">
    <div class="sidebar">
      <div class="sidebar-section">
        <div class="sidebar-title">📂 File Upload</div>
        <form method="POST" enctype="multipart/form-data" action="{{ url_for('upload_file') }}">
          <input type="file" name="file">
          <button type="submit">Upload</button>
        </form>
      </div>
      <div class="sidebar-section">
        <div class="sidebar-title">🃏 Flashcards</div>
        <form method="POST" action="{{ url_for('generate_flashcards') }}">
          <input type="text" name="topic" placeholder="Enter topic" required>
          <select name="subject">
            <option value="science">Science</option>
            <option value="math">Math</option>
            <option value="history">History</option>
          </select>
          <button type="submit">Generate</button>
        </form>
      </div>
    </div>

    <div class="chat-area">
      <div class="chat-header"><div class="chat-title">Chat with PhenBOT</div></div>
      <div class="chat-messages" id="chat-messages"></div>
      <div class="chat-input">
        <form method="POST" action="{{ url_for('ask') }}">
          <div class="controls-row">
            <select name="subject">
              <option value="general">General</option>
              <option value="math">Math</option>
              <option value="science">Science</option>
            </select>
            <select name="mode">
              <option value="normal">Normal</option>
              <option value="analogy">Analogy</option>
              <option value="quiz">Quiz</option>
            </select>
            <select name="length_preference">
              <option value="short">Short</option>
              <option value="normal">Normal</option>
              <option value="detailed">Detailed</option>
            </select>
          </div>
          <textarea class="input-field" name="question" placeholder="Type your question"></textarea>
          <button class="send-btn" type="submit">Ask</button>
        </form>
      </div>
    </div>
  </div>
</body>
</html>
"""

# -------------------- Routes --------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template_string(MAIN_APP_HTML)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user(request.form['username'])
        if user and check_password_hash(user[2], request.form['password']):
            session['user_id'], session['username'] = user[0], user[1]
            return redirect(url_for('index'))
        flash("Invalid login", "error")
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if create_user(request.form['username'], request.form['password']):
            flash("Account created! Please login", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already exists", "error")
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/ask', methods=['POST'])
def ask():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    question = request.form['question']
    subject = request.form.get('subject', 'general')
    mode = request.form.get('mode', 'normal')
    length_pref = request.form.get('length_preference', 'normal')
    # call AI here (placeholder)
    answer = f"PhenBOT ({subject}, {mode}, {length_pref}): {question}"
    return render_template_string(MAIN_APP_HTML, answer=answer)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        flash("File uploaded", "success")
    return redirect(url_for('index'))

@app.route('/flashcards', methods=['POST'])
def generate_flashcards():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    topic = request.form['topic']
    subject = request.form.get('subject', 'general')
    flash(f"Generated flashcards for {topic} ({subject})", "success")
    return redirect(url_for('index'))

# -------------------- Run --------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
