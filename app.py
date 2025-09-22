from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import traceback
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import traceback
from datetime import datetime
from functools import wraps

# Create Flask app instance
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database setup
DATABASE = 'phenbot.db'

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

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
        return False  # Username already exists
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

# Initialize database on startup
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
    """Initialize Groq client with error handling"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    if not GROQ_IMPORT_SUCCESS:
        GROQ_ERROR = 'Groq SDK not installed'
        GROQ_AVAILABLE = False
        print("Groq SDK not available")
        return
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        GROQ_ERROR = 'GROQ_API_KEY environment variable missing'
        GROQ_AVAILABLE = False
        print("GROQ_API_KEY not set")
        return
    
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
    except Exception as e:
        GROQ_ERROR = str(e)
        GROQ_AVAILABLE = False
        print(f"Groq initialization failed: {e}")

initialize_groq()

def get_ai_response(question, subject):
    """Get AI response from Groq"""
    if not groq_client:
        return "AI system is currently unavailable. Please check the server configuration."
    
    system_prompts = {
        'math': 'You are PhenBOT, a mathematics tutor. Provide clear, step-by-step explanations with examples.',
        'science': 'You are PhenBOT, a science tutor. Explain concepts using real-world analogies and examples.',
        'english': 'You are PhenBOT, an English tutor. Help with grammar, writing, and literature analysis.',
        'history': 'You are PhenBOT, a history tutor. Present information through engaging narratives.',
        'general': 'You are PhenBOT, a smart AI study assistant. Provide helpful, educational answers.'
    }
    
    system_prompt = system_prompts.get(subject, system_prompts['general'])
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return f"Error processing your question: {str(e)}"

# Authentication helpers
def is_logged_in():
    return 'user_id' in session and 'username' in session

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
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
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 420px;
            }
            .logo {
                text-align: center;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .tagline {
                text-align: center;
                color: #64748b;
                margin-bottom: 2rem;
            }
            h2 {
                margin-bottom: 2rem;
                color: #1e293b;
                text-align: center;
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: #374151;
            }
            input {
                width: 100%;
                padding: 0.875rem;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 16px;
                transition: all 0.3s ease;
            }
            input:focus {
                outline: none;
                border-color: #4facfe;
                box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
            }
            .btn {
                width: 100%;
                padding: 0.875rem;
                background: linear-gradient(135deg, #4facfe, #00f2fe);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(79, 172, 254, 0.3);
            }
            .link-section {
                text-align: center;
                margin-top: 1.5rem;
                padding-top: 1.5rem;
                border-top: 1px solid #e5e7eb;
            }
            .link-section a {
                color: #4facfe;
                text-decoration: none;
                font-weight: 500;
            }
            .link-section a:hover {
                text-decoration: underline;
            }
            .flash-messages {
                margin-bottom: 1rem;
            }
            .flash {
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }
            .flash.error {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }
            .flash.success {
                background: #f0fdf4;
                color: #16a34a;
                border: 1px solid #bbf7d0;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="logo">🤖</div>
            <h2>Welcome to PhenBOT</h2>
            <p class="tagline">Your AI Study Companion</p>
            
            <div class="flash-messages">
                {% for category, message in get_flashed_messages(with_categories=true) %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required 
                           value="{{ request.form.username if request.form.username }}">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn">Sign In</button>
            </form>
            
            <div class="link-section">
                <p>Don't have an account? <a href="{{ url_for('register') }}">Create one here</a></p>
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
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 420px;
            }
            .logo {
                text-align: center;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .tagline {
                text-align: center;
                color: #64748b;
                margin-bottom: 2rem;
            }
            h2 {
                margin-bottom: 2rem;
                color: #1e293b;
                text-align: center;
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: #374151;
            }
            input {
                width: 100%;
                padding: 0.875rem;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 16px;
                transition: all 0.3s ease;
            }
            input:focus {
                outline: none;
                border-color: #4facfe;
                box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
            }
            .btn {
                width: 100%;
                padding: 0.875rem;
                background: linear-gradient(135deg, #4facfe, #00f2fe);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(79, 172, 254, 0.3);
            }
            .link-section {
                text-align: center;
                margin-top: 1.5rem;
                padding-top: 1.5rem;
                border-top: 1px solid #e5e7eb;
            }
            .link-section a {
                color: #4facfe;
                text-decoration: none;
                font-weight: 500;
            }
            .link-section a:hover {
                text-decoration: underline;
            }
            .flash-messages {
                margin-bottom: 1rem;
            }
            .flash {
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }
            .flash.error {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }
            .flash.success {
                background: #f0fdf4;
                color: #16a34a;
                border: 1px solid #bbf7d0;
            }
            .requirements {
                font-size: 0.875rem;
                color: #64748b;
                margin-top: 0.5rem;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="logo">🤖</div>
            <h2>Join PhenBOT</h2>
            <p class="tagline">Create your study companion account</p>
            
            <div class="flash-messages">
                {% for category, message in get_flashed_messages(with_categories=true) %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required minlength="3"
                           value="{{ request.form.username if request.form.username }}">
                    <div class="requirements">At least 3 characters</div>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required minlength="6">
                    <div class="requirements">At least 6 characters</div>
                </div>
                <button type="submit" class="btn">Create Account</button>
            </form>
            
            <div class="link-section">
                <p>Already have an account? <a href="{{ url_for('login') }}">Sign in here</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

    MAIN_APP_HTML = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PhenBOT - Study Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --secondary-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                --accent-color: #4facfe;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --error-color: #ef4444;
                --card-bg: #ffffff;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --border-color: #e2e8f0;
                --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--primary-gradient);
                min-height: 100vh;
                color: var(--text-primary);
            }
            .app-container { display: flex; height: 100vh; overflow: hidden; }
            
            .sidebar {
                width: 280px;
                background: var(--card-bg);
                border-right: 1px solid var(--border-color);
                display: flex;
                flex-direction: column;
            }
            .sidebar-header {
                padding: 20px;
                background: var(--secondary-gradient);
                color: white;
            }
            .logo { font-size: 24px; font-weight: 700; margin-bottom: 5px; }
            .tagline { font-size: 14px; opacity: 0.9; }
            .nav-tabs { padding: 20px 0; flex: 1; }
            .nav-tab {
                display: flex;
                align-items: center;
                padding: 12px 20px;
                color: var(--text-secondary);
                border-left: 3px solid transparent;
                cursor: pointer;
                background: none;
                border: none;
                width: 100%;
                text-align: left;
                font-size: 14px;
                transition: all 0.2s ease;
            }
            .nav-tab:hover,
            .nav-tab.active {
                background: rgba(79, 172, 254, 0.1);
                color: var(--accent-color);
                border-left-color: var(--accent-color);
            }
            .nav-tab-icon { margin-right: 12px; font-size: 16px; width: 20px; text-align: center; }
            .user-section {
                padding: 20px;
                border-top: 1px solid var(--border-color);
                background: #f8fafc;
            }
            .user-info {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
            }
            .user-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: var(--secondary-gradient);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
            }
            .logout-btn {
                width: 100%;
                padding: 8px 16px;
                background: var(--error-color);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                text-decoration: none;
                text-align: center;
                display: block;
            }
            
            .main-content { flex: 1; display: flex; flex-direction: column; }
            .top-bar {
                background: var(--card-bg);
                padding: 16px 24px;
                border-bottom: 1px solid var(--border-color);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .system-status {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
            }
            .system-status:hover { transform: scale(1.05); }
            .system-status.online { background: var(--success-color); color: white; }
            .system-status.offline { background: var(--error-color); color: white; }
            .system-status.checking { background: var(--warning-color); color: white; }
            
            .content-area { flex: 1; padding: 24px; overflow-y: auto; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            
            .chat-container {
                background: var(--card-bg);
                border-radius: 16px;
                box-shadow: var(--shadow);
                height: 75vh;
                display: flex;
                flex-direction: column;
            }
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                scroll-behavior: smooth;
            }
            .message {
                margin-bottom: 20px;
                display: flex;
                gap: 12px;
                align-items: flex-start;
                animation: slideIn 0.3s ease;
            }
            .message.user { flex-direction: row-reverse; }
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .message-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                flex-shrink: 0;
            }
            .message.bot .message-avatar {
                background: var(--secondary-gradient);
                color: white;
            }
            .message.user .message-avatar {
                background: var(--primary-gradient);
                color: white;
            }
            .message-content {
                max-width: 75%;
                padding: 12px 16px;
                border-radius: 16px;
                line-height: 1.6;
                white-space: pre-wrap;
            }
            .message.bot .message-content {
                background: #f1f5f9;
                border-bottom-left-radius: 4px;
            }
            .message.user .message-content {
                background: var(--accent-color);
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .chat-input-area {
                padding: 20px;
                border-top: 1px solid var(--border-color);
            }
            .input-container {
                display: flex;
                gap: 12px;
                align-items: flex-end;
            }
            .message-input {
                flex: 1;
                min-height: 50px;
                max-height: 120px;
                padding: 12px 16px;
                border: 2px solid var(--border-color);
                border-radius: 24px;
                outline: none;
                font-size: 16px;
                resize: none;
                font-family: inherit;
                transition: border-color 0.3s ease;
            }
            .message-input:focus {
                border-color: var(--accent-color);
                box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
            }
            .send-button {
                background: var(--secondary-gradient);
                color: white;
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                transition: transform 0.2s ease;
            }
            .send-button:hover:not(:disabled) { transform: scale(1.05); }
            .send-button:disabled { opacity: 0.6; cursor: not-allowed; }
            
            @media (max-width: 768px) {
                .app-container { flex-direction: column; }
                .sidebar { width: 100%; height: auto; }
                .chat-container { height: 60vh; }
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <div class="sidebar">
                <div class="sidebar-header">
                    <div class="logo">🤖 PhenBOT</div>
                    <div class="tagline">Advanced Study Companion</div>
                </div>
                
                <nav class="nav-tabs">
                    <button class="nav-tab active" data-tab="math">
                        <span class="nav-tab-icon">🔢</span>Mathematics
                    </button>
                    <button class="nav-tab" data-tab="science">
                        <span class="nav-tab-icon">🔬</span>Science
                    </button>
                    <button class="nav-tab" data-tab="english">
                        <span class="nav-tab-icon">📚</span>English
                    </button>
                    <button class="nav-tab" data-tab="history">
                        <span class="nav-tab-icon">🏛️</span>History
                    </button>
                </nav>
                
                <div class="user-section">
                    <div class="user-info">
                        <div class="user-avatar">{{ username[0].upper() }}</div>
                        <div>
                            <div style="font-weight: 600;">{{ username }}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Student</div>
                        </div>
                    </div>
                    <a href="{{ url_for('logout') }}" class="logout-btn">Sign Out</a>
                </div>
            </div>
            
            <div class="main-content">
                <div class="top-bar">
                    <div class="system-status checking" id="systemStatus">🔄 Checking AI...</div>
                    <div style="font-size: 14px; color: var(--text-secondary);">
                        {{ datetime.now().strftime('%B %d, %Y') }}
                    </div>
                </div>
                
                <div class="content-area">
                    <div class="tab-content active" id="math">
                        <div class="chat-container">
                            <div class="chat-messages" id="mathMessages">
                                <div class="message bot">
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">Welcome to Mathematics! I'm here to help you understand concepts through step-by-step explanations. What mathematical topic would you like to explore?</div>
                                </div>
                            </div>
                            <div class="chat-input-area">
                                <div class="input-container">
                                    <textarea class="message-input" placeholder="Ask a math question..." data-subject="math"></textarea>
                                    <button class="send-button" disabled>➤</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tab-content" id="science">
                        <div class="chat-container">
                            <div class="chat-messages" id="scienceMessages">
                                <div class="message bot">
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">Ready to explore Science! I can explain complex concepts using real-world examples and analogies. What scientific topic interests you?</div>
                                </div>
                            </div>
                            <div class="chat-input-area">
                                <div class="input-container">
                                    <textarea class="message-input" placeholder="Ask a science question..." data-subject="science"></textarea>
                                    <button class="send-button" disabled>➤</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tab-content" id="english">
                        <div class="chat-container">
                            <div class="chat-messages" id="englishMessages">
                                <div class="message bot">
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">Let's work on English & Literature! I can help with grammar, writing techniques, literary analysis, and language concepts. What can I help you with?</div>
                                </div>
                            </div>
                            <div class="chat-input-area">
                                <div class="input-container">
                                    <textarea class="message-input" placeholder="Ask about English/Literature..." data-subject="english"></textarea>
                                    <button class="send-button" disabled>➤</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tab-content" id="history">
                        <div class="chat-container">
                            <div class="chat-messages" id="historyMessages">
                                <div class="message bot">
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">Welcome to History! I'll help you understand historical events, their causes, and connections to the present. What period or topic would you like to explore?</div>
                                </div>
                            </div>
                            <div class="chat-input-area">
                                <div class="input-container">
                                    <textarea class="message-input" placeholder="Ask a history question..." data-subject="history"></textarea>
                                    <button class="send-button" disabled>➤</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let isSystemReady = false;

            // Tab switching functionality
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    const targetTab = tab.dataset.tab;
                    
                    // Update active tab
                    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    // Show target content
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    document.getElementById(targetTab).classList.add('active');
                });
            });

            // Input handling
            document.querySelectorAll('.message-input').forEach(input => {
                const sendButton = input.parentNode.querySelector('.send-button');
                
                input.addEventListener('input', () => {
                    sendButton.disabled = input.value.trim() === '';
                });
                
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (input.value.trim() !== '') {
                            sendMessage(input);
                        }
                    }
                });
                
                sendButton.addEventListener('click', () => {
                    if (input.value.trim() !== '') {
                        sendMessage(input);
                    }
                });
            });

            function addMessage(messagesContainer, content, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
                
                messageDiv.innerHTML = `
                    <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
                    <div class="message-content">${content}</div>
                `;
                
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            function sendMessage(input) {
                const subject = input.dataset.subject;
                const question = input.value.trim();
                const messagesContainer = document.getElementById(subject + 'Messages');
                const sendButton = input.parentNode.querySelector('.send-button');
                
                // Add user message
                addMessage(messagesContainer, question, true);
                
                // Clear input and disable send button
                input.value = '';
                sendButton.disabled = true;
                
                // Show loading state
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message bot';
                loadingDiv.id = 'loading-message';
                loadingDiv.innerHTML = `
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">Thinking...</div>
                `;
                messagesContainer.appendChild(loadingDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                // Send to backend
                fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: question,
                        subject: subject
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Remove loading message
                    const loadingMessage = document.getElementById('loading-message');
                    if (loadingMessage) {
                        loadingMessage.remove();
                    }
                    
                    // Add bot response
                    addMessage(messagesContainer, data.response);
                })
                .catch(error => {
                    console.error('Error:', error);
                    
                    // Remove loading message
                    const loadingMessage = document.getElementById('loading-message');
                    if (loadingMessage) {
                        loadingMessage.remove();
                    }
                    
                    // Add error message
                    addMessage(messagesContainer, 'Sorry, there was an error processing your request. Please try again.');
                });
            }

            // Check AI system status
            function checkSystemStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusElement = document.getElementById('systemStatus');
                        if (data.groq_available) {
                            statusElement.className = 'system-status online';
                            statusElement.innerHTML = '🟢 AI Online';
                            isSystemReady = true;
                        } else {
                            statusElement.className = 'system-status offline';
                            statusElement.innerHTML = '🔴 AI Offline';
                            isSystemReady = false;
                        }
                    })
                    .catch(error => {
                        console.error('Status check error:', error);
                        const statusElement = document.getElementById('systemStatus');
                        statusElement.className = 'system-status offline';
                        statusElement.innerHTML = '🔴 Connection Error';
                        isSystemReady = false;
                    });
            }

            // Initial status check
            checkSystemStatus();
            
            // Check status every 30 seconds
            setInterval(checkSystemStatus, 30000);
        </script>
    </body>
    </html>

# Routes
@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template_string(LOGIN_HTML)
        
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template_string(REGISTER_HTML)
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template_string(REGISTER_HTML)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template_string(REGISTER_HTML)
        
        if create_user(username, password):
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists. Please choose another.', 'error')
    
    return render_template_string(REGISTER_HTML)

@app.route('/dashboard')
@require_login
def dashboard():
    return render_template_string(MAIN_APP_HTML, 
                                username=session['username'],
                                datetime=datetime)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
@require_login
def api_chat():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        response = get_ai_response(question, subject)
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Chat API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status')
def api_status():
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'groq_error': GROQ_ERROR if not GROQ_AVAILABLE else None
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'groq_available': GROQ_AVAILABLE
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
'''
