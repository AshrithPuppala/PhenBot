# Complete PhenBOT Application - app.py
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import traceback
from datetime import datetime
import json
import PyPDF2
import io

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database setup
DATABASE = 'phenbot.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    """Initialize database with enhanced tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chat history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            mode TEXT,
            length_preference TEXT,
            question TEXT,
            answer TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Uploaded files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            original_filename TEXT,
            file_path TEXT,
            file_type TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Flashcards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            front TEXT,
            back TEXT,
            subject TEXT,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text content from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def get_user(username):
    """Get user by username"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    """Create a new user"""
    try:
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      (username, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def save_chat_history(user_id, subject, mode, length_preference, question, answer):
    """Save chat interaction to database"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (user_id, subject, mode, length_preference, question, answer)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, subject, mode, length_preference, question, answer))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving chat history: {e}")

def save_flashcard(user_id, title, front, back, subject, difficulty):
    """Save flashcard to database"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO flashcards (user_id, title, front, back, subject, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, front, back, subject, difficulty))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving flashcard: {e}")
        return False

# Initialize database
init_db()

# Groq AI Setup
try:
    from groq import Groq
    GROQ_IMPORT_SUCCESS = True
except ImportError:
    GROQ_IMPORT_SUCCESS = False

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initialize Groq client"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    if not GROQ_IMPORT_SUCCESS:
        GROQ_ERROR = 'Groq SDK not installed'
        GROQ_AVAILABLE = False
        print("Warning: Groq SDK not available - AI features will be limited")
        return
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        GROQ_ERROR = 'GROQ_API_KEY environment variable missing'
        GROQ_AVAILABLE = False
        print("Warning: GROQ_API_KEY not set - AI features will be limited")
        return
    
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("✅ Groq client initialized successfully")
    except Exception as e:
        GROQ_ERROR = str(e)
        GROQ_AVAILABLE = False
        print(f"Warning: Groq initialization failed: {e}")

# Initialize Groq
initialize_groq()

def get_ai_response(question, subject, mode, length_preference, context=None):
    """Enhanced AI response with modes and length preferences"""
    if not groq_client:
        return "AI system is currently unavailable. Please check your GROQ_API_KEY environment variable."
    
    # Base system prompts for subjects
    subject_prompts = {
        'math': 'You are PhenBOT, a mathematics tutor.',
        'science': 'You are PhenBOT, a science educator.',  
        'english': 'You are PhenBOT, an English and literature tutor.',
        'history': 'You are PhenBOT, a history educator.',
        'general': 'You are PhenBOT, an AI study assistant.'
    }
    
    # Mode-specific instructions
    mode_instructions = {
        'normal': 'Provide clear, direct explanations.',
        'analogy': 'Explain concepts using creative analogies and real-world comparisons. Make complex ideas easier to understand through relatable examples.',
        'quiz': 'Create engaging quiz questions based on the topic. Provide multiple choice or short answer questions with explanations.',
        'teach': 'Act as a patient teacher. Break down concepts step-by-step, check for understanding, and provide practice examples.',
        'socratic': 'Use the Socratic method - guide learning through thoughtful questions rather than direct answers.',
        'summary': 'Provide concise summaries and key points. Focus on the most important information.'
    }
    
    # Length preferences
    length_instructions = {
        'short': 'Keep your response concise - 2-3 sentences maximum.',
        'normal': 'Provide a moderate length response - 1-2 paragraphs.',
        'detailed': 'Give a comprehensive, detailed explanation with examples and additional context.'
    }
    
    # Build the system prompt
    base_prompt = subject_prompts.get(subject, subject_prompts['general'])
    mode_instruction = mode_instructions.get(mode, mode_instructions['normal'])
    length_instruction = length_instructions.get(length_preference, length_instructions['normal'])
    
    system_prompt = f"{base_prompt} {mode_instruction} {length_instruction}"
    
    # Add context if provided
    if context:
        system_prompt += f" Use this context to inform your response: {context[:1000]}..."
    
    try:
        # Adjust max_tokens based on length preference
        token_limits = {
            'short': 150,
            'normal': 400, 
            'detailed': 800
        }
        
        max_tokens = token_limits.get(length_preference, 400)
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return f"Error processing your question: {str(e)}"

def generate_flashcards_from_topic(topic, subject, difficulty, count=5):
    """Generate flashcards from a topic"""
    if not groq_client:
        return []
    
    prompt = f"""
    Create {count} educational flashcards about {topic} in {subject} at {difficulty} difficulty level.
    
    Format each flashcard as:
    FRONT: [Question or concept]
    BACK: [Answer or explanation]
    ---
    
    Make the flashcards comprehensive and educational.
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        flashcards = []
        
        # Parse flashcards
        cards = content.split('---')
        for card in cards:
            if 'FRONT:' in card and 'BACK:' in card:
                lines = card.strip().split('\n')
                front = ""
                back = ""
                current_side = None
                
                for line in lines:
                    if line.startswith('FRONT:'):
                        current_side = 'front'
                        front = line.replace('FRONT:', '').strip()
                    elif line.startswith('BACK:'):
                        current_side = 'back'
                        back = line.replace('BACK:', '').strip()
                    elif current_side == 'front':
                        front += " " + line.strip()
                    elif current_side == 'back':
                        back += " " + line.strip()
                
                if front and back:
                    flashcards.append({
                        'front': front.strip(),
                        'back': back.strip()
                    })
        
        return flashcards[:count]
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

def generate_flashcards_from_text(text, subject, difficulty, count=5):
    """Generate flashcards from text content"""
    if not groq_client:
        return []
    
    prompt = f"""
    Create {count} flashcards from the following text for {subject} at {difficulty} difficulty level.
    
    Text: {text[:2000]}...
    
    Format each flashcard as:
    FRONT: [Question or concept]
    BACK: [Answer or explanation]
    ---
    
    Make the flashcards educational and appropriate for the difficulty level.
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        
        content = response.choices[0].message.content
        flashcards = []
        
        # Parse the response into flashcards
        cards = content.split('---')
        for card in cards:
            if 'FRONT:' in card and 'BACK:' in card:
                lines = card.strip().split('\n')
                front = ""
                back = ""
                current_side = None
                
                for line in lines:
                    if line.startswith('FRONT:'):
                        current_side = 'front'
                        front = line.replace('FRONT:', '').strip()
                    elif line.startswith('BACK:'):
                        current_side = 'back'
                        back = line.replace('BACK:', '').strip()
                    elif current_side == 'front':
                        front += " " + line.strip()
                    elif current_side == 'back':
                        back += " " + line.strip()
                
                if front and back:
                    flashcards.append({
                        'front': front.strip(),
                        'back': back.strip()
                    })
        
        return flashcards[:count]
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

# Authentication helpers
def is_logged_in():
    return 'user_id' in session and 'username' in session

def require_login(f):
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# HTML Templates
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #667eea;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .logo p {
            color: #666;
            font-size: 1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
        }
        .flash-messages {
            margin-bottom: 1rem;
        }
        .flash-message {
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .flash-error {
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        .flash-success {
            background: #efe;
            color: #393;
            border: 1px solid #cfc;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <h1>🤖 PhenBOT</h1>
            <p>Your AI Study Assistant</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <div class="links">
            <a href="{{ url_for('register') }}">Don't have an account? Sign up</a>
        </div>
    </div>
</body>
</html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT Register</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #667eea;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .logo p {
            color: #666;
            font-size: 1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
        }
        .flash-messages {
            margin-bottom: 1rem;
        }
        .flash-message {
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .flash-error {
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        .flash-success {
            background: #efe;
            color: #393;
            border: 1px solid #cfc;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <h1>🤖 PhenBOT</h1>
            <p>Create Your Account</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required minlength="3">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="links">
            <a href="{{ url_for('login') }}">Already have an account? Sign in</a>
        </div>
    </div>
</body>
</html>
'''

# Complete Main Dashboard HTML with all features
MAIN_APP_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT - AI Study Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .logo { 
            font-size: 1.5rem; 
            font-weight: 700; 
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .main-container {
            display: flex;
            margin-top: 80px;
            min-height: calc(100vh - 80px);
        }
        
        .sidebar {
            width: 350px;
            background: white;
            box-shadow: 4px 0 20px rgba(0,0,0,0.1);
            padding: 2rem 1rem;
            overflow-y: auto;
        }
        
        .sidebar-section { 
            margin-bottom: 2rem; 
        }
        
        .sidebar-title { 
            font-size: 1.1rem; 
            font-weight: 600; 
            margin-bottom: 1rem; 
            color: #333; 
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
            margin: 1rem;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-title { 
            font-size: 1.3rem; 
            font-weight: 600; 
        }
        
        .chat-messages {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
            max-height: 500px;
            background: #f8fafc;
        }
        
        .message { 
            margin-bottom: 1.5rem;
            animation: fadeIn 0.3s ease-in;
        }
        
        .message-user { 
            text-align: right; 
        }
        
        .message-content {
            display: inline-block;
            max-width: 80%;
            padding: 1rem 1.5rem;
            border-radius: 20px;
            word-wrap: break-word;
        }
        
        .message-user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .message-bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #e1e5e9;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .message-info {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
        }
        
        .chat-input {
            padding: 2rem;
            background: white;
            border-top: 1px solid #e1e5e9;
        }
        
        .controls-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .control-group { 
            display: flex; 
            flex-direction: column; 
        }
        
        .control-label { 
            font-size: 0.9rem; 
            font-weight: 500; 
            margin-bottom: 0.5rem; 
            color: #555; 
        }
        
        .control-select {
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            background: white;
            font-size: 0.9rem;
            transition: border-color 0.3s;
        }
        
        .control-select:focus { 
            outline: none; 
            border-color: #667eea; 
        }
        
        .input-group { 
            display: flex; 
            gap: 1rem; 
            margin-bottom: 1rem;
        }
        
        .input-field {
            flex: 1;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 1rem;
            resize: none;
            min-height: 60px;
            transition: border-color 0.3s;
        }
        
        .input-field:focus { 
            outline: none; 
            border-color: #667eea; 
        }
        
        .send-btn {
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2
