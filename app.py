from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import traceback
import PyPDF2
import io
import base64
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database setup
DATABASE = 'phenbot.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

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
        return
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        GROQ_ERROR = 'GROQ_API_KEY environment variable missing'
        GROQ_AVAILABLE = False
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

def get_ai_response(question, subject, mode, length_preference, context=None):
    """Enhanced AI response with modes and length preferences"""
    if not groq_client:
        return "AI system is currently unavailable. Please check the server configuration."
    
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
    
    # Add context if provided (for PDF processing)
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
        
        return flashcards[:count]  # Limit to requested count
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

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
        
        # Parse flashcards (same parsing logic as above)
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

# Routes will be in Part 2...# Continue from Part 1 - add these routes to the app.py file

# Main Routes
@app.route('/')
def index():
    if is_logged_in():
        return render_template_string(MAIN_APP_HTML, 
                                    username=session['username'],
                                    datetime=datetime)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
        else:
            user = get_user(username)
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Successfully logged in!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
    
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
        elif len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
        else:
            if create_user(username, password):
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Username already exists', 'error')
    
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

# API Endpoints
@app.route('/health')
def health():
    return jsonify({
        'healthy': True,
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/ask', methods=['POST'])
@require_login
def api_ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        mode = data.get('mode', 'normal')
        length_preference = data.get('length', 'normal')
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'AI system unavailable: {GROQ_ERROR}'}), 503
        
        # Get AI response
        answer = get_ai_response(question, subject, mode, length_preference)
        
        # Save to chat history
        save_chat_history(session['user_id'], subject, mode, length_preference, question, answer)
        
        return jsonify({
            'answer': answer,
            'mode': mode,
            'length': length_preference,
            'subject': subject
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/api/upload', methods=['POST'])
@require_login
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        unique_filename = timestamp + filename
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Extract text if PDF
        extracted_text = None
        if filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)
        
        # Save file info to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploaded_files (user_id, filename, original_filename, file_path, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], unique_filename, filename, file_path, 
              filename.rsplit('.', 1)[1].lower()))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'text_extracted': bool(extracted_text),
            'text_length': len(extracted_text) if extracted_text else 0
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/summarize_pdf', methods=['POST'])
@require_login
def summarize_pdf():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({'error': 'File ID required'}), 400
        
        # Get file info
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM uploaded_files WHERE id = ? AND user_id = ?', 
                      (file_id, session['user_id']))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'File not found'}), 404
        
        # Extract text
        text = extract_text_from_pdf(result[0])
        if not text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Generate summary
        summary_prompt = f"Provide a comprehensive summary of this document:\n\n{text[:3000]}..."
        summary = get_ai_response(summary_prompt, 'general', 'summary', 'detailed')
        
        return jsonify({
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary)
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Summarization failed'}), 500

@app.route('/api/generate_flashcards', methods=['POST'])
@require_login
def api_generate_flashcards():
    try:
        data = request.get_json()
        source_type = data.get('source_type', 'topic')  # 'topic' or 'file'
        
        if source_type == 'file':
            file_id = data.get('file_id')
            if not file_id:
                return jsonify({'error': 'File ID required'}), 400
            
            # Get file and extract text
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM uploaded_files WHERE id = ? AND user_id = ?', 
                          (file_id, session['user_id']))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return jsonify({'error': 'File not found'}), 404
            
            text = extract_text_from_pdf(result[0])
            if not text:
                return jsonify({'error': 'Could not extract text from file'}), 400
            
            subject = data.get('subject', 'general')
            difficulty = data.get('difficulty', 'medium')
            count = min(data.get('count', 5), 10)  # Max 10 flashcards
            
            flashcards = generate_flashcards_from_text(text, subject, difficulty, count)
            
        else:  # topic-based
            topic = data.get('topic', '').strip()
            if not topic:
                return jsonify({'error': 'Topic required'}), 400
            
            subject = data.get('subject', 'general')
            difficulty = data.get('difficulty', 'medium')
            count = min(data.get('count', 5), 10)
            
            flashcards = generate_flashcards_from_topic(topic, subject, difficulty, count)
        
        # Save flashcards if requested
        if data.get('save_flashcards', False):
            title = data.get('title', f"Flashcards - {datetime.now().strftime('%Y-%m-%d')}")
            for card in flashcards:
                save_flashcard(session['user_id'], title, card['front'], card['back'], 
                             subject, difficulty)
        
        return jsonify({
            'flashcards': flashcards,
            'count': len(flashcards)
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Flashcard generation failed'}), 500

@app.route('/api/save_flashcard', methods=['POST'])
@require_login
def api_save_flashcard():
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        front = data.get('front', '').strip()
        back = data.get('back', '').strip()
        subject = data.get('subject', 'general')
        difficulty = data.get('difficulty', 'medium')
        
        if not front or not back:
            return jsonify({'error': 'Front and back content required'}), 400
        
        if save_flashcard(session['user_id'], title, front, back, subject, difficulty):
            return jsonify({'success': True, 'message': 'Flashcard saved successfully'})
        else:
            return jsonify({'error': 'Failed to save flashcard'}), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Save failed'}), 500

@app.route('/api/get_flashcards')
@require_login
def api_get_flashcards():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, front, back, subject, difficulty, created_at
            FROM flashcards WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 50
        ''', (session['user_id'],))
        
        flashcards = []
        for row in cursor.fetchall():
            flashcards.append({
                'id': row[0],
                'title': row[1],
                'front': row[2],
                'back': row[3],
                'subject': row[4],
                'difficulty': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return jsonify({'flashcards': flashcards})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Failed to load flashcards'}), 500

@app.route('/api/chat_history')
@require_login
def api_chat_history():
    try:
        subject = request.args.get('subject', None)
        limit = min(int(request.args.get('limit', 20)), 100)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        if subject:
            cursor.execute('''
                SELECT question, answer, mode, length_preference, timestamp
                FROM chat_history WHERE user_id = ? AND subject = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (session['user_id'], subject, limit))
        else:
            cursor.execute('''
                SELECT question, answer, mode, length_preference, timestamp, subject
                FROM chat_history WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (session['user_id'], limit))
        
        history = []
        for row in cursor.fetchall():
            item = {
                'question': row[0],
                'answer': row[1],
                'mode': row[2],
                'length': row[3],
                'timestamp': row[4]
            }
            if not subject:
                item['subject'] = row[5]
            history.append(item)
        
        conn.close()
        return jsonify({'history': history})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Failed to load chat history'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return redirect(url_for('login'))

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return redirect(url_for('login'))

# Add requirements.txt content:
REQUIREMENTS_TXT = '''
Flask==2.3.3
Werkzeug==2.3.7
groq==0.4.1
gunicorn==21.2.0
PyPDF2==3.0.1
python-dotenv==1.0.0
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Enhanced PhenBOT on port {port}")
    print(f"Groq available: {GROQ_AVAILABLE}")
    if GROQ_ERROR:
        print(f"Groq error: {GROQ_ERROR}")
    app.run(host='0.0.0.0', port=port, debug=False)
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
            overflow-x: hidden;
        }
        
        /* Header */
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
            backdrop-filter: blur(10px);
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
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .user-name {
            font-weight: 500;
        }
        
        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
            text-decoration: none;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        /* Main Container */
        .main-container {
            display: flex;
            margin-top: 80px;
            min-height: calc(100vh - 80px);
        }
        
        /* Sidebar */
        .sidebar {
            width: 300px;
            background: white;
            box-shadow: 4px 0 20px rgba(0,0,0,0.1);
            padding: 2rem 1rem;
            overflow-y: auto;
            border-radius: 0 20px 0 0;
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
        
        /* Chat Area */
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
        
        .chat-controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        /* Chat Messages */
        .chat-messages {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
            max-height: 60vh;
            background: #f8fafc;
        }
        
        .message {
            margin-bottom: 1.5rem;
            animation: fadeIn 0.3s ease-in;
            display:flex;
            gap:12px;
            align-items:flex-start;
        }
        
        .message .avatar {
            width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; color:white;
        }
        .avatar.user { background: linear-gradient(135deg,#667eea,#764ba2); }
        .avatar.bot { background: linear-gradient(135deg,#10b981,#06b6d4); }

        .message-content {
            display: inline-block;
            max-width: 78%;
            padding: 1rem 1.2rem;
            border-radius: 14px;
            word-wrap: break-word;
            line-height:1.45;
            font-size: 1rem;
        }
        
        .message-user { justify-content:flex-end; }
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
        
        .message-meta {
            font-size: 0.78rem;
            color:#666;
            margin-top:6px;
        }
        
        /* Chat Input */
        .chat-input {
            padding: 2rem;
            background: white;
            border-top: 1px solid #e1e5e9;
        }
        
        .input-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            align-items:stretch;
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
        
        .controls-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
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
        
        .send-btn {
            padding: 1rem 1.25rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .send-btn:disabled { opacity:0.6; cursor:not-allowed; }
        
        /* Pomodoro Timer */
        .pomodoro-timer {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 1rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .timer-display {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .timer-controls {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
        }
        
        .timer-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .timer-status {
            font-size: 0.9rem;
            margin-top: 0.5rem;
            opacity: 0.9;
        }
        
        /* File Upload */
        .file-upload {
            margin-bottom: 1rem;
        }
        
        .file-drop-zone {
            border: 2px dashed #667eea;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            background: #f8fafc;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .file-drop-zone.drag-over {
            background: #e6eefc;
            border-color: #3b82f6;
        }
        
        .file-input {
            display: none;
        }
        
        .file-info {
            margin-top: 1rem;
            padding: 1rem;
            background: #e0f2fe;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        
        /* Flashcards */
        .flashcard {
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }
        
        .flashcard.flipped { transform: rotateY(180deg); background:#f0f9ff; border-color:#0ea5e9; }
        
        .flashcard-content { font-size: 1.05rem; text-align:center; }
        .flashcard-hint { font-style:italic; color:#666; text-align:center; margin-top:8px; }
        
        /* Buttons */
        .btn {
            padding: 0.6rem 1rem;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }
        
        .btn-primary { background: linear-gradient(135deg,#667eea,#764ba2); color:white; }
        .btn-secondary { background:#f1f5f9; color:#475569; border:1px solid #e2e8f0; }
        .btn-success { background: linear-gradient(135deg,#10b981,#059669); color:white; }
        .btn-danger { background: linear-gradient(135deg,#ef4444,#dc2626); color:white; }
        
        .voice-btn { width:48px; height:48px; border-radius:50%; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; color:white; background:linear-gradient(135deg,#10b981,#059669); }
        .voice-btn.recording { background: linear-gradient(135deg,#ef4444,#dc2626); animation: pulse 1s infinite; }
        
        /* Toast & Modal */
        .toast { position: fixed; right: 20px; bottom: 20px; background: #111827; color: white; padding: 12px 16px; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); z-index: 3000; opacity:0; transform: translateY(12px); transition: all 0.25s; }
        .toast.show { opacity:1; transform: translateY(0); }
        
        .modal-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:2000; align-items:center; justify-content:center; padding:1rem; }
        .modal-overlay.show { display:flex; }
        .modal { background:white; border-radius:12px; max-width:900px; width:100%; max-height:90vh; overflow:auto; padding:1rem; }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .sidebar { width: 250px; }
        }
        
        @media (max-width: 768px) {
            .main-container { flex-direction: column; }
            .sidebar { width:100%; border-radius:0; }
            .chat-area { margin: 0.5rem; }
        }
        
        @keyframes fadeIn { from { opacity:0; transform: translateY(10px) } to { opacity:1; transform:none } }
        @keyframes pulse { 0%,100%{ transform:scale(1) } 50%{ transform:scale(1.06) } }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <div class="logo">🤖 PhenBOT</div>
            <div class="user-info">
                <span class="user-name">Welcome, {{ username }}!</span>
                <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <!-- Pomodoro Timer -->
            <div class="sidebar-section">
                <div class="sidebar-title">🍅 Focus Timer</div>
                <div class="pomodoro-timer">
                    <div class="timer-display" id="timerDisplay">25:00</div>
                    <div class="timer-controls">
                        <button class="timer-btn" id="timerStartBtn">Start</button>
                        <button class="timer-btn" id="timerPauseBtn">Pause</button>
                        <button class="timer-btn" id="timerResetBtn">Reset</button>
                    </div>
                    <div class="timer-status" id="timerStatus">Ready to focus</div>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="sidebar-section">
                <div class="sidebar-title">📊 Today's Stats</div>
                <div style="background: white; padding: 1rem; border-radius: 10px; font-size: 0.9rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                        <div>Questions</div><div id="statQuestions">0</div>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                        <div>Focus Sessions</div><div id="statSessions">0</div>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <div>Flashcards</div><div id="statFlashcards">0</div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="sidebar-section">
                <div class="sidebar-title">⚡ Quick Actions</div>
                <div style="display:flex;flex-direction:column;gap:8px;">
                    <button class="btn btn-primary" id="clearChatBtn">Clear Chat</button>
                    <button class="btn btn-secondary" id="exportChatBtn">Export Chat</button>
                    <button class="btn btn-success" id="openFlashcardModal">Open Flashcards</button>
                </div>
            </div>

            <!-- Theme -->
            <div class="sidebar-section">
                <div class="sidebar-title">🎨 Theme</div>
                <div style="display:flex;gap:8px;align-items:center;">
                    <label style="display:flex;gap:8px;align-items:center;cursor:pointer;">
                        <input id="themeToggle" type="checkbox" style="transform:scale(1.2)"/> Dark
                    </label>
                </div>
            </div>
        </div>

        <!-- Chat Area -->
        <div class="chat-area">
            <div class="chat-header">
                <div style="display:flex;gap:12px;align-items:center;">
                    <div class="chat-title">AI Study Assistant</div>
                    <div class="chat-controls">
                        <select id="chatMode" class="control-select" title="Chat mode">
                            <option value="normal">Normal</option>
                            <option value="analogy">Analogy</option>
                            <option value="quiz">Quiz</option>
                            <option value="teach">Teaching</option>
                            <option value="socratic">Socratic</option>
                            <option value="explain">ELI5</option>
                            <option value="summary">Summary</option>
                        </select>

                        <select id="responseLength" class="control-select" title="Response length">
                            <option value="short">Short</option>
                            <option value="normal" selected>Normal</option>
                            <option value="detailed">Detailed</option>
                        </select>

                        <div class="voice-controls">
                            <button id="voiceBtn" class="voice-btn" title="Voice input"><span id="voiceIcon">🎙️</span></button>
                        </div>
                    </div>
                </div>

                <div style="display:flex;gap:12px;align-items:center;">
                    <div id="aiStatus" style="font-size:0.95rem;color:rgba(255,255,255,0.9)">AI Online</div>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <!-- sample bot welcome -->
                <div class="message message-bot">
                    <div class="avatar bot">B</div>
                    <div>
                        <div class="message-content">Hello! I'm PhenBOT — your AI study companion. Choose a mode and ask me anything, or upload a PDF to analyze it.</div>
                        <div class="message-meta">Just now</div>
                    </div>
                </div>
            </div>

            <div class="chat-input">
                <div class="controls-row">
                    <div class="control-group">
                        <label class="control-label">Attach PDF (drag & drop)</label>
                        <div id="dropZone" class="file-drop-zone">Drop PDF here or <button class="btn btn-secondary" id="selectFileBtn">Select File</button></div>
                        <input id="fileInput" class="file-input" type="file" accept="application/pdf" />
                        <div id="fileInfo" class="file-info" style="display:none;"></div>
                        <div style="margin-top:8px;display:flex;gap:8px;">
                            <button id="summarizeFileBtn" class="btn btn-primary">Summarize File</button>
                            <button id="generateFlashcardsBtn" class="btn btn-success">Generate Flashcards</button>
                        </div>
                    </div>

                    <div class="control-group">
                        <label class="control-label">Keyboard Shortcuts</label>
                        <div style="font-size:0.9rem;color:#555;">
                            <div>Ctrl+K: Focus input</div>
                            <div>Ctrl+L: Clear chat</div>
                            <div>Ctrl+U: Upload file</div>
                        </div>
                    </div>
                </div>

                <div style="display:flex;gap:12px;align-items:flex-end;">
                    <textarea id="messageInput" class="input-field" placeholder="Ask me anything — Enter to send, Shift+Enter for newline"></textarea>
                    <div style="display:flex;flex-direction:column;gap:8px;">
                        <button id="sendBtn" class="send-btn">Send</button>
                        <button id="moreBtn" class="btn btn-secondary" title="More actions">⋯</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Flashcard Modal -->
    <div id="flashcardModal" class="modal-overlay" aria-hidden="true">
        <div class="modal" role="dialog" aria-modal="true">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h3>Flashcard Library</h3>
                <button id="closeFlashcardModal" class="close-btn">✕</button>
            </div>
            <div style="margin-top:12px;">
                <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;">
                    <input id="flashTopic" placeholder="Topic (optional)" style="flex:1;padding:8px;border-radius:6px;border:1px solid #e1e5e9" />
                    <select id="flashDifficulty" style="padding:8px;border-radius:6px;border:1px solid #e1e5e9;">
                        <option value="easy">Easy</option>
                        <option value="medium" selected>Medium</option>
                        <option value="hard">Hard</option>
                    </select>
                    <button id="generateTopicFlashcards" class="btn btn-primary">Generate</button>
                </div>

                <div id="flashcardsContainer"></div>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div id="toast" class="toast" role="status" aria-live="polite"></div>

    <script>
    (function(){
        // Basic refs
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const chatMode = document.getElementById('chatMode');
        const responseLength = document.getElementById('responseLength');
        const voiceBtn = document.getElementById('voiceBtn');
        const voiceIcon = document.getElementById('voiceIcon');
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const summarizeFileBtn = document.getElementById('summarizeFileBtn');
        const generateFlashcardsBtn = document.getElementById('generateFlashcardsBtn');
        const toastEl = document.getElementById('toast');
        const timerDisplay = document.getElementById('timerDisplay');
        const timerStartBtn = document.getElementById('timerStartBtn');
        const timerPauseBtn = document.getElementById('timerPauseBtn');
        const timerResetBtn = document.getElementById('timerResetBtn');
        const timerStatus = document.getElementById('timerStatus');
        const statQuestions = document.getElementById('statQuestions');
        const statSessions = document.getElementById('statSessions');
        const statFlashcards = document.getElementById('statFlashcards');
        const clearChatBtn = document.getElementById('clearChatBtn');
        const exportChatBtn = document.getElementById('exportChatBtn');
        const openFlashcardModalBtn = document.getElementById('openFlashcardModal');
        const flashcardModal = document.getElementById('flashcardModal');
        const closeFlashcardModal = document.getElementById('closeFlashcardModal');
        const generateTopicFlashcards = document.getElementById('generateTopicFlashcards');
        const flashcardsContainer = document.getElementById('flashcardsContainer');
        const flashTopic = document.getElementById('flashTopic');
        const flashDifficulty = document.getElementById('flashDifficulty');
        const themeToggle = document.getElementById('themeToggle');
        const selectFileBtn = document.getElementById('selectFileBtn');

        // State
        let conversationHistory = []; // saved in localStorage optionally
        let stats = { questions:0, sessions:0, flashcards:0 };
        let voiceRec = null;
        let isRecording = false;
        // Pomodoro state
        let pomodoroInterval = null;
        let pomodoroSeconds = 25 * 60;
        let pomodoroRunning = false;
        let inBreak = false;

        // Utility: show toast
        function showToast(msg, time=3000){
            toastEl.textContent = msg;
            toastEl.classList.add('show');
            setTimeout(()=> toastEl.classList.remove('show'), time);
        }

        // Append message
        function appendMessage({role, text, meta}){
            const msg = document.createElement('div');
            msg.className = 'message ' + (role === 'user' ? 'message-user' : 'message-bot');
            const avatar = document.createElement('div');
            avatar.className = 'avatar ' + (role === 'user' ? 'user' : 'bot');
            avatar.textContent = role === 'user' ? 'U' : 'B';
            const contentWrap = document.createElement('div');
            const content = document.createElement('div');
            content.className = 'message-content';
            // basic safety: escape < to prevent HTML injection
            content.innerHTML = String(text).replaceAll('<','&lt;').replaceAll('\\n','<br>').replaceAll('\\r','');
            const metaEl = document.createElement('div');
            metaEl.className = 'message-meta';
            metaEl.textContent = meta || new Date().toLocaleString();
            contentWrap.appendChild(content);
            contentWrap.appendChild(metaEl);
            msg.appendChild(avatar);
            msg.appendChild(contentWrap);
            chatMessages.appendChild(msg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Send chat request to backend
        async function sendChat(){
            const message = messageInput.value.trim();
            if(!message) return;
            appendMessage({role:'user', text:message});
            messageInput.value = '';
            // stats
            stats.questions += 1;
            saveStats();
            updateStatsUI();

            // show typing indicator
            const typing = document.createElement('div');
            typing.className = 'message message-bot';
            typing.innerHTML = '<div class="avatar bot">B</div><div><div class="message-content">...</div><div class="message-meta">Thinking...</div></div>';
            chatMessages.appendChild(typing);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            const payload = { message, mode: chatMode.value, length: responseLength.value };
            try {
                const res = await fetch('/api/chat', {
                    method:'POST',
                    headers:{ 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                typing.remove();
                if(data.error){
                    appendMessage({role:'bot', text: 'Error: ' + data.error});
                    showToast('AI Error: ' + (data.error||'unknown'));
                } else {
                    appendMessage({role:'bot', text: data.reply || '[no reply]'});
                    // speak reply
                    speakText(data.reply || '');
                }
            } catch (err){
                typing.remove();
                appendMessage({role:'bot', text:'Network error: ' + err.message});
            }
        }

        sendBtn.addEventListener('click', sendChat);

        // keyboard handling
        messageInput.addEventListener('keydown', (e) => {
            if(e.key === 'Enter' && !e.shiftKey){
                e.preventDefault();
                sendChat();
            }
            // Ctrl shortcuts
            if(e.ctrlKey && e.key.toLowerCase() === 'k'){
                e.preventDefault();
                messageInput.focus();
            }
        });

        // global shortcuts
        document.addEventListener('keydown', (e) => {
            if(e.ctrlKey && e.key.toLowerCase() === 'l'){
                e.preventDefault();
                clearChat();
            }
            if(e.ctrlKey && e.key.toLowerCase() === 'u'){
                e.preventDefault();
                fileInput.click();
            }
            if(e.ctrlKey && e.key.toLowerCase() === 'k'){
                e.preventDefault();
                messageInput.focus();
            }
        });

        // Voice recording via Web Speech API
        function initVoice(){
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRecognition) {
                voiceBtn.style.display = 'none';
                return;
            }
            voiceRec = new SpeechRecognition();
            voiceRec.lang = 'en-US';
            voiceRec.interimResults = false;
            voiceRec.onresult = (ev) => {
                const text = Array.from(ev.results).map(r=>r[0].transcript).join('');
                messageInput.value = text;
                sendChat();
            };
            voiceRec.onend = () => {
                isRecording = false;
                voiceBtn.classList.remove('recording');
            };
            voiceRec.onerror = (e) => {
                isRecording = false;
                voiceBtn.classList.remove('recording');
                showToast('Voice error: ' + e.error);
            };
        }

        voiceBtn.addEventListener('click', ()=>{
            if(!voiceRec) return;
            if(!isRecording){
                isRecording = true;
                voiceBtn.classList.add('recording');
                voiceRec.start();
            } else {
                isRecording = false;
                voiceBtn.classList.remove('recording');
                voiceRec.stop();
            }
        });

        function speakText(text){
            if(!('speechSynthesis' in window)) return;
            try {
                const u = new SpeechSynthesisUtterance(text);
                u.lang = 'en-US';
                u.rate = 1;
                window.speechSynthesis.speak(u);
            } catch(e) { console.warn('speak error', e); }
        }

        // File upload + drag/drop
        dropZone.addEventListener('dragover', (e)=>{ e.preventDefault(); dropZone.classList.add('drag-over'); });
        dropZone.addEventListener('dragleave', ()=> dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e)=> {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const f = e.dataTransfer.files && e.dataTransfer.files[0];
            if(f) handleSelectedFile(f);
        });

        selectFileBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            const f = e.target.files && e.target.files[0];
            if(f) handleSelectedFile(f);
        });

        function handleSelectedFile(f){
            if(!f.name.toLowerCase().endsWith('.pdf')) { showToast('Please select a PDF'); return; }
            fileInfo.style.display = 'block';
            fileInfo.textContent = 'Selected: ' + f.name + ' (' + Math.round(f.size/1024) + ' KB)';
            fileInput._file = f;
        }

        async function processFile(action){
            const f = fileInput._file;
            if(!f) { showToast('Upload a PDF first'); return; }
            showToast('Processing PDF — this may take a few seconds');
            const form = new FormData();
            form.append('file', f);
            form.append('action', action);
            if(action === 'flashcards') {
                form.append('num_cards', 12);
                form.append('difficulty', 'medium');
            }
            try {
                const res = await fetch('/api/process_pdf', { method:'POST', body: form });
                const data = await res.json();
                if(data.error) {
                    showToast('PDF error: ' + data.error);
                    appendMessage({role:'bot', text: 'PDF error: ' + data.error});
                } else if(action === 'summarize') {
                    appendMessage({role:'bot', text: 'PDF Summary:\\n' + (data.summary || '[no summary]')});
                } else if(action === 'flashcards') {
                    if(data.flashcards && Array.isArray(data.flashcards)){
                        // add to UI and stats
                        stats.flashcards += data.flashcards.length;
                        saveStats();
                        updateStatsUI();
                        showToast('Added ' + data.flashcards.length + ' flashcards to library');
                        renderFlashcards(data.flashcards);
                    } else {
                        appendMessage({role:'bot', text: data.raw || JSON.stringify(data)});
                    }
                }
            } catch (err) {
                showToast('Network error: ' + err.message);
            }
        }

        summarizeFileBtn.addEventListener('click', ()=> processFile('summarize'));
        generateFlashcardsBtn.addEventListener('click', ()=> processFile('flashcards'));

        // Flashcard modal
        openFlashcardModalBtn.addEventListener('click', ()=> { flashcardModal.classList.add('show'); flashcardModal.setAttribute('aria-hidden','false'); });
        closeFlashcardModal.addEventListener('click', ()=> { flashcardModal.classList.remove('show'); flashcardModal.setAttribute('aria-hidden','true'); });

        // Generate flashcards by topic from AI
        generateTopicFlashcards.addEventListener('click', async ()=>{
            const topic = flashTopic.value.trim();
            const difficulty = flashDifficulty.value || 'medium';
            if(!topic) { showToast('Please enter a topic to generate flashcards'); return; }
            showToast('Generating flashcards for ' + topic);
            // reuse /api/chat to request flashcards (simple prompt)
            const prompt = `Generate 8 short flashcards (JSON array) on the topic "${topic}" with difficulty ${difficulty}. Each card: {"question":"...","answer":"...","difficulty":"..."} - return only JSON.`;
            try {
                const res = await fetch('/api/chat', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({ message: prompt, mode: 'teach', length: 'short' })
                });
                const data = await res.json();
                if(data.reply){
                    // try parse JSON from reply
                    let arr = [];
                    try {
                        const match = data.reply.match(/(\\[.*\\])/s);
                        arr = match ? JSON.parse(match[1]) : JSON.parse(data.reply);
                    } catch(e){
                        // fallback: display text
                        appendMessage({ role:'bot', text: 'Could not parse generated flashcards. Response:\\n' + data.reply });
                        return;
                    }
                    stats.flashcards += arr.length;
                    saveStats();
                    updateStatsUI();
                    renderFlashcards(arr);
                    showToast('Generated ' + arr.length + ' flashcards');
                } else {
                    showToast('No reply from AI');
                }
            } catch(err){
                showToast('Error: ' + err.message);
            }
        });

        // Render flashcards in modal
        function renderFlashcards(cards){
            flashcardsContainer.innerHTML = '';
            (cards||[]).forEach((c, idx) => {
                const card = document.createElement('div');
                card.className = 'flashcard';
                card.innerHTML = '<div class="flashcard-content"><strong>' + escapeHtml(c.question || c.q || ('Card ' + (idx+1))) + '</strong><div class="flashcard-hint">' + escapeHtml(c.difficulty || c.level || '') + '</div></div>';
                card.dataset.answer = c.answer || c.a || '';
                card.addEventListener('click', () => {
                    if(card.classList.contains('flipped')){
                        card.classList.remove('flipped');
                        card.innerHTML = '<div class="flashcard-content"><strong>' + escapeHtml(c.question || c.q || ('Card ' + (idx+1))) + '</strong><div class="flashcard-hint">' + escapeHtml(c.difficulty || c.level || '') + '</div></div>';
                    } else {
                        card.classList.add('flipped');
                        card.innerHTML = '<div class="flashcard-content"><strong>' + escapeHtml(c.answer || c.a || 'Answer') + '</strong></div>';
                    }
                });
                flashcardsContainer.appendChild(card);
            });
        }

        // Escape helper
        function escapeHtml(s){ if(!s) return ''; return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }

        // Clear & Export
        clearChatBtn.addEventListener('click', clearChat);
        function clearChat(){
            chatMessages.innerHTML = '';
            appendMessage({role:'bot', text: "Chat cleared. Ready when you are!"});
            conversationHistory = [];
            localStorage.removeItem('phenbot_conversation');
        }

        exportChatBtn.addEventListener('click', ()=>{
            const text = Array.from(chatMessages.querySelectorAll('.message')).map(m=>{
                const who = m.classList.contains('message-user') ? 'User' : 'Bot';
                const content = m.querySelector('.message-content')?.innerText || '';
                const meta = m.querySelector('.message-meta')?.innerText || '';
                return who + ' [' + meta + ']:\\n' + content;
            }).join('\\n\\n');
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'phenbot_chat.txt'; document.body.appendChild(a); a.click(); a.remove();
            URL.revokeObjectURL(url);
            showToast('Chat exported');
        });

        // Save/load stats
        function loadStats(){
            const raw = localStorage.getItem('phenbot_stats');
            if(raw) try { stats = JSON.parse(raw); } catch(e){}
            updateStatsUI();
        }
        function saveStats(){ localStorage.setItem('phenbot_stats', JSON.stringify(stats)); }

        function updateStatsUI(){
            statQuestions.textContent = stats.questions || 0;
            statSessions.textContent = stats.sessions || 0;
            statFlashcards.textContent = stats.flashcards || 0;
        }

        // Pomodoro functions
        function formatTime(s){
            const m = Math.floor(s/60); const sec = s%60;
            return String(m).padStart(2,'0') + ':' + String(sec).padStart(2,'0');
        }
        function startTimer(){
            if(pomodoroRunning) return;
            pomodoroRunning = true;
            pomodoroInterval = setInterval(()=>{
                if(pomodoroSeconds <= 0){
                    clearInterval(pomodoroInterval);
                    pomodoroRunning = false;
                    // session finished
                    stats.sessions = (stats.sessions || 0) + 1;
                    saveStats(); updateStatsUI();
                    showToast(inBreak ? 'Break ended — back to focus!' : 'Focus session finished — time for break!');
                    // toggle between break/focus
                    inBreak = !inBreak;
                    pomodoroSeconds = inBreak ? 5*60 : 25*60;
                    timerStatus.textContent = inBreak ? 'On Break' : 'Focus mode';
                    // auto-start next? not doing that by default
                } else {
                    pomodoroSeconds -= 1;
                    timerDisplay.textContent = formatTime(pomodoroSeconds);
                }
            }, 1000);
            timerStatus.textContent = 'Running';
        }
        function pauseTimer(){
            if(pomodoroInterval) clearInterval(pomodoroInterval);
            pomodoroRunning = false;
            timerStatus.textContent = 'Paused';
        }
        function resetTimer(){
            if(pomodoroInterval) clearInterval(pomodoroInterval);
            pomodoroRunning = false;
            inBreak = false;
            pomodoroSeconds = 25*60;
            timerDisplay.textContent = formatTime(pomodoroSeconds);
            timerStatus.textContent = 'Ready to focus';
        }

        timerStartBtn.addEventListener('click', startTimer);
        timerPauseBtn.addEventListener('click', pauseTimer);
        timerResetBtn.addEventListener('click', resetTimer);

        // Theme toggle
        function applyTheme(dark){
            if(dark) document.documentElement.classList.add('dark-theme');
            else document.documentElement.classList.remove('dark-theme');
            localStorage.setItem('phenbot_dark', dark ? '1' : '0');
        }
        themeToggle.addEventListener('change', (e)=> applyTheme(e.target.checked));
        // load theme preference
        const savedDark = localStorage.getItem('phenbot_dark') === '1';
        themeToggle.checked = savedDark; applyTheme(savedDark);

        // Init
        function init(){
            initVoice();
            loadStats();
            // restore conversation? (optional)
            const conv = localStorage.getItem('phenbot_conversation');
            if(conv){
                try {
                    const parsed = JSON.parse(conv);
                    parsed.forEach(m => appendMessage(m));
                } catch(e){}
            }
        }
        init();

        // Autosave conversation every 10s
        setInterval(()=> {
            const nodes = Array.from(chatMessages.querySelectorAll('.message'));
            const toSave = nodes.map(n => {
                return {
                    role: n.classList.contains('message-user') ? 'user' : 'bot',
                    text: n.querySelector('.message-content')?.innerText || '',
                    meta: n.querySelector('.message-meta')?.innerText || ''
                };
            });
            localStorage.setItem('phenbot_conversation', JSON.stringify(toSave));
        }, 10000);

    })();
    </script>
</body>
</html>
'''
