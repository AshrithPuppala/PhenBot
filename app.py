from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils import *
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with a strong key in production

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    if 'email' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        secret_code = request.form['secret_code']
        success, msg = register_user(email, secret_code)
        flash(msg)
        if success:
            return redirect(url_for('login'))
    return render_template('register.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        secret_code = request.form['secret_code']
        user = authenticate_user(email, secret_code)
        if user:
            session['email'] = email
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('login.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    flashcards = load_flashcards(email)
    history = load_history(email)
    return render_template('dashboard.html', flashcards=flashcards, history=history)

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('home'))

# ---------- CREATE FLASHCARD ----------
@app.route('/flashcard/create', methods=['POST'])
def create_flashcard_route():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    question = request.form['question']
    answer = request.form['answer']
    subject = request.form['subject']
    create_flashcard(email, question, answer, subject)
    flash("Flashcard created!")
    return redirect(url_for('dashboard'))

# ---------- UPLOAD PDF ----------
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    if 'pdf' not in request.files:
        flash("No file selected")
        return redirect(url_for('dashboard'))
    file = request.files['pdf']
    path = save_pdf(file, email)
    if path:
        flash("PDF uploaded successfully!")
    else:
        flash("Invalid file type")
    return redirect(url_for('dashboard'))

# ---------- AI QUERY (OPTIONAL) ----------
@app.route('/ask', methods=['POST'])
def ask_ai():
    if 'email' not in session:
        return redirect(url_for('login'))
    question = request.form['question']
    # Here you integrate OpenAI API or your AI backend
    answer = f"Simulated AI answer for: {question}"
    update_history(session['email'], questions_asked=1)
    flash(answer)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
