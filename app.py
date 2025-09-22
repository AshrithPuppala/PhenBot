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

# Routes will be in Part 2...
# Continue from Part 1 - add these routes to the app.py file

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
    # Part 3: Complete Enhanced Frontend HTML Templates (add to app.py)

# Complete the LOGIN_HTML template
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
            backdrop-filter: blur(10px);
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

# Register HTML template
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
            backdrop-filter: blur(10px);
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

# Main App HTML Template with Enhanced Features
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
            max-height: 600px;
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
            display: flex;
            align-items: center;
            gap: 0.5rem;
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
        
        .send-btn:hover:not(:disabled) {
            transform: translateY(-2px);
        }
        
        .send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        /* Controls */
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
            transition: background 0.3s;
        }
        
        .timer-btn:hover {
            background: rgba(255,255,255,0.3);
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
            padding: 2rem;
            text-align: center;
            background: #f8fafc;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .file-drop-zone:hover {
            background: #f1f5f9;
            border-color: #4c63d2;
        }
        
        .file-drop-zone.drag-over {
            background: #e0e7ff;
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
            padding: 1.5rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }
        
        .flashcard:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .flashcard.flipped {
            background: #f0f9ff;
            border-color: #0ea5e9;
        }
        
        .flashcard-content {
            font-size: 1.1rem;
            line-height: 1.5;
            text-align: center;
        }
        
        .flashcard-hint {
            font-size: 0.8rem;
            color: #666;
            text-align: center;
            margin-top: 1rem;
            font-style: italic;
        }
        
        /* Buttons */
        .btn {
            padding: 0.75rem 1.5rem;
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
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Voice Chat */
        .voice-controls {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        .voice-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .voice-btn:hover {
            transform: scale(1.1);
        }
        
        .voice-btn.recording {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            animation: pulse 1s infinite;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        /* Loading States */
        .loading {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #e1e5e9;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .sidebar {
                width: 250px;
            }
        }
        
        @media (max-width: 768px) {
            .header-content {
                padding: 0 1rem;
            }
            
            .main-container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                padding: 1rem;
                border-radius: 0;
            }
            
            .chat-area {
                margin: 0.5rem;
                border-radius: 15px;
            }
            
            .controls-row {
                grid-template-columns: 1fr;
            }
        }
        
        /* Success/Error Messages */
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        .alert-info {
            background: #e0f2fe;
            color: #0c4a6e;
            border: 1px solid #7dd3fc;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 2px solid #e1e5e9;
            margin-bottom: 1rem;
        }
        
        .tab {
            padding: 0.75rem 1.5rem;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom: 2px solid #667eea;
        }
        
        .tab:hover {
            color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <div class="logo">
                🤖 PhenBOT
            </div>
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
                        <button class="timer-btn" onclick="startTimer()">Start</button>
                        <button class="timer-btn" onclick="pauseTimer()">Pause</button>
                        <button class="timer-btn" onclick="resetTimer()">Reset</button>
                    </div>
                    <div class="timer-status" id="timerStatus">Ready to focus</div>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="sidebar-section">
                <div class="sidebar-title">📊 Today's Stats</div>
                <div style="background: white; padding: 1rem; border-radius: 10px; font-size: 0.9rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Questions Asked:</span>
                        <strong id="questionsCount">0</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Focus Sessions:</span>
                        <strong id="focusCount">0</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Flashcards Created:</span>
                        <strong id="flashcardsCount">0</strong>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="sidebar-section">
                <div class="sidebar-title">⚡ Quick Actions</div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <button class="btn btn-secondary" onclick="clearChat()">🗑️ Clear Chat</button>
                    <button class="btn btn-secondary" onclick="exportChat()">📥 Export Chat</button>
                    <button class="btn btn-secondary" onclick="showHistory()">📜 View History</button>
                </div>
            </div>
        </div>

        <!-- Main Chat Area -->
        <div class="chat-area">
            <div class="chat-header">
                <div class="chat-title">AI Study Assistant</div>
                <div class="chat-controls">
                    <div class="voice-controls">
                        <button class="voice-btn" id="voiceBtn" onclick="toggleVoiceRecording()" title="Voice Input">
                            🎤
                        </button>
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="message message-bot">
                    <div class="message-content">
                        👋 Hello {{ username }}! I'm PhenBOT, your AI study assistant. I'm here to help you learn, understand complex topics, create flashcards, and boost your productivity. What would you like to explore today?
                    </div>
                    <div class="message-info">
                        <span>🤖 PhenBOT</span>
                        <span>•</span>
                        <span>{{ datetime.now().strftime('%H:%M') }}</span>
                    </div>
                </div>
            </div>

            <div class="chat-input">
                <!-- File Upload Area -->
                <div class="file-upload" style="display: none;" id="fileUploadArea">
                    <div class="file-drop-zone" id="fileDropZone" onclick="document.getElementById('fileInput').click()">
                        <div>📄 Drop your PDF file here or click to browse</div>
                        <div style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">Supports PDF, TXT, DOC files up to 16MB</div>
                    </div>
                    <input type="file" id="fileInput" class="file-input" accept=".pdf,.txt,.doc,.docx">
                    <div class="file-info" id="fileInfo" style="display: none;"></div>
                </div>

                <!-- Main Controls -->
                <div class="controls-row">
                    <div class="control-group">
                        <label class="control-label">📚 Subject</label>
                        <select class="control-select" id="subjectSelect">
                            <option value="general">General</option>
                            <option value="math">Mathematics</option>
                            <option value="science">Science</option>
                            <option value="english">English/Literature</option>
                            <option value="history">History</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label class="control-label">🎯 AI Mode</label>
                        <select class="control-select" id="modeSelect">
                            <option value="normal">Normal</option>
                            <option value="analogy">Analogy Mode</option>
                            <option value="quiz">Quiz Mode</option>
                            <option value="teach">Teaching Mode</option>
                            <option value="socratic">Socratic Method</option>
                            <option value="summary">Summary Mode</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label class="control-label">📏 Response Length</label>
                        <select class="control-select" id="lengthSelect">
                            <option value="short">Short</option>
                            <option value="normal">Normal</option>
                            <option value="detailed">Detailed</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label class="control-label">🔧 Tools</label>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-secondary" onclick="toggleFileUpload()" id="uploadToggle">📎 Upload</button>
                            <button class="btn btn-secondary" onclick="showFlashcards()">🃏 Cards</button>
                        </div>
                    </div>
                </div>

                <!-- Input Area -->
                <div class="input-group">
                    <textarea 
                        class="input-field" 
                        id="messageInput" 
                        placeholder="Ask me anything... (e.g., 'Explain photosynthesis using analogies' or 'Create flashcards about the French Revolution')"
                        rows="3"></textarea>
                    <button class="send-btn" id="sendBtn" onclick="sendMessage()">
                        <span id="sendBtnText">Send</span>
                        <span>🚀</span>
                    </button>
                </div>

                <!-- Quick Prompts -->
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1rem;">
                    <button class="btn btn-secondary" onclick="quickPrompt('Explain this concept simply')">💡 Explain Simply</button>
                    <button class="btn btn-secondary" onclick="quickPrompt('Create a quiz on this topic')">❓ Make Quiz</button>
                    <button class="btn btn-secondary" onclick="quickPrompt('Give me practice problems')">📝 Practice</button>
                    <button class="btn btn-secondary" onclick="quickPrompt('Summarize the key points')">📋 Summarize</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Flashcards Modal -->
    <div id="flashcardsModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 2000; padding: 2rem;">
        <div style="background: white; border-radius: 20px; max-width: 800px; margin: 0 auto; height: 80vh; overflow: hidden; display: flex; flex-direction: column;">
            <div style="padding: 2rem; border-bottom: 1px solid #e1e5e9; display: flex; justify-content: space-between; align-items: center;">
                <h2>🃏 Flashcards</h2>
                <button onclick="closeFlashcards()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
            </div>
            
            <div style="flex: 1; padding: 2rem; overflow-y: auto;">
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('create')">Create</button>
                    <button class="tab" onclick="switchTab('study')">Study</button>
                    <button class="tab" onclick="switchTab('library')">Library</button>
                </div>
                
                <!-- Create Tab -->
                <div class="tab-content active" id="createTab">
                    <div style="margin-bottom: 2rem;">
                        <h3>Generate Flashcards</h3>
                        <div class="controls-row" style="margin-bottom: 1rem;">
                            <div class="control-group">
                                <label class="control-label">Topic or Upload File</label>
                                <input type="text" id="flashcardTopic" class="input-field" placeholder="e.g., World War II, Algebra, Cell Biology">
                            </div>
                            <div class="control-group">
                                <label class="control-label">Difficulty</label>
                                <select class="control-select" id="flashcardDifficulty">
                                    <option value="easy">Easy</option>
                                    <option value="medium">Medium</option>
                                    <option value="hard">Hard</option>
                                </select>
                            </div>
                            <div class="control-group">
                                <label class="control-label">Count</label>
                                <select class="control-select" id="flashcardCount">
                                    <option value="5">5 Cards</option>
                                    <option value="10">10 Cards</option>
                                    <option value="15">15 Cards</option>
                                </select>
                            </div>
                        </div>
                        <div style="display: flex; gap: 1rem;">
                            <button class="btn btn-primary" onclick="generateFlashcards()">🎯 Generate from Topic</button>
                            <button class="btn btn-secondary" onclick="generateFromFile()">📄 Generate from File</button>
                        </div>
                    </div>
                    
                    <div id="generatedFlashcards"></div>
                </div>
                
                <!-- Study Tab -->
                <div class="tab-content" id="studyTab">
                    <div id="studyArea">
                        <div style="text-align: center; padding: 2rem; color: #666;">
                            Select flashcards from your library to start studying
                        </div>
                    </div>
                </div>
                
                <!-- Library Tab -->
                <div class="tab-content" id="libraryTab">
                    <div id="flashcardLibrary">
                        <div style="text-align: center; padding: 2rem; color: #666;">
                            <div class="spinner"></div>
                            Loading your flashcards...
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script>
        // Global variables
        let timerInterval;
        let timerSeconds = 25 * 60; // 25 minutes
        let isTimerRunning = false;
        let currentFlashcardIndex = 0;
        let studyFlashcards = [];
        let isRecording = false;
        let recognition;
        let questionsAsked = 0;
        let focusSessions = 0;
        let flashcardsCreated = 0;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            setupVoiceRecognition();
            setupFileUpload();
            loadStats();
            
            // Auto-resize textarea
            const messageInput = document.getElementById('messageInput');
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
            
            // Enter key handling
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        });

        // Voice Recognition Setup
        function setupVoiceRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('messageInput').value = transcript;
                };
                
                recognition.onend = function() {
                    isRecording = false;
                    document.getElementById('voiceBtn').classList.remove('recording');
                    document.getElementById('voiceBtn').innerHTML = '🎤';
                };
            } else {
                document.getElementById('voiceBtn').style.display = 'none';
            }
        }

        // Voice Recording Toggle
        function toggleVoiceRecording() {
            if (!recognition) return;
            
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
                isRecording = true;
                document.getElementById('voiceBtn').classList.add('recording');
                document.getElementById('voiceBtn').innerHTML = '⏹️';
            }
        }

        // File Upload Setup
        function setupFileUpload() {
            const fileInput = document.getElementById('fileInput');
            const dropZone = document.getElementById('fileDropZone');
            
            fileInput.addEventListener('change', handleFileSelect);
            
            // Drag and drop
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });
            
            dropZone.addEventListener('dragleave', function() {
                dropZone.classList.remove('drag-over');
            });
            
            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileSelect({target: {files: files}});
                }
            });
        }

        // Handle File Selection
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const fileInfo = document.getElementById('fileInfo');
            fileInfo.style.display = 'block';
            fileInfo.innerHTML = `
                <div><strong>Selected:</strong> ${file.name}</div>
                <div><strong>Size:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB</div>
                <div style="margin-top: 0.5rem;">
                    <button class="btn btn-primary" onclick="uploadFile()">📤 Upload & Process</button>
                    <button class="btn btn-secondary" onclick="clearFile()">❌ Remove</button>
                </div>
            `;
        }

        // Upload File
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (response.ok && data.flashcards) {
                    displayGeneratedFlashcards(data.flashcards);
                    flashcardsCreated += data.flashcards.length;
                    updateStats();
                    addMessage(`✅ Created ${data.flashcards.length} flashcards from your file!`, 'bot');
                } else {
                    alert('Failed to generate flashcards: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        function askAboutFile(fileId) {
            const question = prompt('What would you like to know about this file?');
            if (question) {
                // Add file context to the question
                document.getElementById('messageInput').value = `About the uploaded file: ${question}`;
                // You could store fileId in a global variable to use in sendMessage
                window.currentFileId = fileId;
            }
        }

        // Additional utility functions
        function generateFromFile() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files[0]) {
                alert('Please upload a file first.');
                return;
            }
            
            // If file is already uploaded, use it
            if (window.currentFileId) {
                generateFlashcardsFromFile(window.currentFileId);
            } else {
                alert('Please upload and process the file first.');
            }
        }

        // Theme toggle (bonus feature)
        function toggleTheme() {
            document.body.classList.toggle('dark-theme');
            localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
        }

        // Load saved theme
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-theme');
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K to focus on input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('messageInput').focus();
            }
            
            // Ctrl/Cmd + L to clear chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
                e.preventDefault();
                clearChat();
            }
            
            // Ctrl/Cmd + U to toggle file upload
            if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
                e.preventDefault();
                toggleFileUpload();
            }
        });

        // Auto-save draft message
        let draftTimer;
        document.getElementById('messageInput').addEventListener('input', function() {
            clearTimeout(draftTimer);
            draftTimer = setTimeout(() => {
                localStorage.setItem('messageDraft', this.value);
            }, 500);
        });

        // Load draft message
        const draft = localStorage.getItem('messageDraft');
        if (draft) {
            document.getElementById('messageInput').value = draft;
        }

        // Clear draft when message is sent
        function clearDraft() {
            localStorage.removeItem('messageDraft');
        }

        // Add to sendMessage function to clear draft
        const originalSendMessage = sendMessage;
        sendMessage = function() {
            clearDraft();
            return originalSendMessage();
        };
    </script>

    <!-- Dark theme CSS (bonus) -->
    <style>
        .dark-theme {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e2e8f0;
        }
        
        .dark-theme .sidebar,
        .dark-theme .chat-area,
        .dark-theme .message-bot .message-content {
            background: #2d3748;
            color: #e2e8f0;
        }
        
        .dark-theme .chat-header {
            background: linear-gradient(135deg, #4c63d2 0%, #5a67d8 100%);
        }
        
        .dark-theme .chat-messages {
            background: #1a202c;
        }
        
        .dark-theme .input-field,
        .dark-theme .control-select {
            background: #2d3748;
            color: #e2e8f0;
            border-color: #4a5568;
        }
        
        .dark-theme .flashcard {
            background: #2d3748;
            border-color: #4a5568;
            color: #e2e8f0;
        }
    </style>
</body>
</html>
'''

# Add this at the end of your app.py file to complete Part 3
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Enhanced PhenBOT v3.0 starting on port {port}")
    print(f"📊 Features: AI Chat, Modes, File Upload, Flashcards, Pomodoro Timer, Voice Input")
    print(f"🤖 Groq AI: {'✅ Ready' if GROQ_AVAILABLE else '❌ ' + str(GROQ_ERROR)}")
    app.run(host='0.0.0.0', port=port, debug=False) (data.success) {
                    const fileInfo = document.getElementById('fileInfo');
                    fileInfo.innerHTML = `
                        <div style="color: #10b981;"><strong>✅ Uploaded:</strong> ${data.filename}</div>
                        <div style="margin-top: 0.5rem;">
                            <button class="btn btn-primary" onclick="summarizeFile(${data.file_id})">📋 Summarize</button>
                            <button class="btn btn-secondary" onclick="generateFlashcardsFromFile(${data.file_id})">🃏 Create Flashcards</button>
                            <button class="btn btn-secondary" onclick="askAboutFile(${data.file_id})">❓ Ask Questions</button>
                        </div>
                    `;
                } else {
                    alert('Upload failed: ' + data.error);
                }
            } catch (error) {
                alert('Upload failed: ' + error.message);
            }
        }

        // Clear File
        function clearFile() {
            document.getElementById('fileInput').value = '';
            document.getElementById('fileInfo').style.display = 'none';
        }

        // Toggle File Upload Area
        function toggleFileUpload() {
            const uploadArea = document.getElementById('fileUploadArea');
            const toggle = document.getElementById('uploadToggle');
            
            if (uploadArea.style.display === 'none') {
                uploadArea.style.display = 'block';
                toggle.textContent = '📎 Hide Upload';
                toggle.classList.add('btn-primary');
                toggle.classList.remove('btn-secondary');
            } else {
                uploadArea.style.display = 'none';
                toggle.textContent = '📎 Upload';
                toggle.classList.remove('btn-primary');
                toggle.classList.add('btn-secondary');
            }
        }

        // Send Message
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            const sendBtn = document.getElementById('sendBtn');
            const sendBtnText = document.getElementById('sendBtnText');
            
            // Disable button and show loading
            sendBtn.disabled = true;
            sendBtnText.innerHTML = '<span class="spinner"></span>';
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            input.style.height = 'auto';
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: message,
                        subject: document.getElementById('subjectSelect').value,
                        mode: document.getElementById('modeSelect').value,
                        length: document.getElementById('lengthSelect').value
                    })
                });
                
                const data = await response.json();
                if (response.ok) {
                    addMessage(data.answer, 'bot', {
                        mode: data.mode,
                        length: data.length,
                        subject: data.subject
                    });
                    questionsAsked++;
                    updateStats();
                } else {
                    addMessage('Error: ' + data.error, 'bot', {error: true});
                }
            } catch (error) {
                addMessage('Connection error: ' + error.message, 'bot', {error: true});
            }
            
            // Re-enable button
            sendBtn.disabled = false;
            sendBtnText.textContent = 'Send';
        }

        // Add Message to Chat
        function addMessage(content, type, meta = {}) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message message-${type}`;
            
            const now = new Date();
            const time = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            let icon = type === 'user' ? '👤' : '🤖';
            let sender = type === 'user' ? 'You' : 'PhenBOT';
            
            if (meta.error) {
                icon = '⚠️';
                content = `<span style="color: #ef4444;">${content}</span>`;
            }
            
            let metaInfo = '';
            if (meta.mode && meta.mode !== 'normal') {
                metaInfo += ` • Mode: ${meta.mode}`;
            }
            if (meta.length && meta.length !== 'normal') {
                metaInfo += ` • Length: ${meta.length}`;
            }
            if (meta.subject && meta.subject !== 'general') {
                metaInfo += ` • Subject: ${meta.subject}`;
            }
            
            messageDiv.innerHTML = `
                <div class="message-content">${content}</div>
                <div class="message-info">
                    <span>${icon} ${sender}</span>
                    <span>•</span>
                    <span>${time}</span>
                    ${metaInfo}
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Quick Prompt
        function quickPrompt(prompt) {
            document.getElementById('messageInput').value = prompt + ': ';
            document.getElementById('messageInput').focus();
        }

        // Pomodoro Timer Functions
        function startTimer() {
            if (!isTimerRunning) {
                isTimerRunning = true;
                document.getElementById('timerStatus').textContent = 'Focus time! 💪';
                timerInterval = setInterval(updateTimer, 1000);
            }
        }

        function pauseTimer() {
            if (isTimerRunning) {
                isTimerRunning = false;
                clearInterval(timerInterval);
                document.getElementById('timerStatus').textContent = 'Paused ⏸️';
            }
        }

        function resetTimer() {
            isTimerRunning = false;
            clearInterval(timerInterval);
            timerSeconds = 25 * 60;
            updateTimerDisplay();
            document.getElementById('timerStatus').textContent = 'Ready to focus';
        }

        function updateTimer() {
            timerSeconds--;
            updateTimerDisplay();
            
            if (timerSeconds <= 0) {
                isTimerRunning = false;
                clearInterval(timerInterval);
                document.getElementById('timerStatus').textContent = 'Great job! Take a break 🎉';
                focusSessions++;
                updateStats();
                
                // Show notification
                if (Notification.permission === 'granted') {
                    new Notification('PhenBOT Timer', {
                        body: 'Focus session completed! Time for a break.',
                        icon: '/favicon.ico'
                    });
                }
                
                // Reset for break (5 minutes)
                timerSeconds = 5 * 60;
                updateTimerDisplay();
            }
        }

        function updateTimerDisplay() {
            const minutes = Math.floor(timerSeconds / 60);
            const seconds = timerSeconds % 60;
            document.getElementById('timerDisplay').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Stats Functions
        function loadStats() {
            questionsAsked = parseInt(localStorage.getItem('questionsAsked') || '0');
            focusSessions = parseInt(localStorage.getItem('focusSessions') || '0');
            flashcardsCreated = parseInt(localStorage.getItem('flashcardsCreated') || '0');
            updateStats();
        }

        function updateStats() {
            document.getElementById('questionsCount').textContent = questionsAsked;
            document.getElementById('focusCount').textContent = focusSessions;
            document.getElementById('flashcardsCount').textContent = flashcardsCreated;
            
            // Save to localStorage
            localStorage.setItem('questionsAsked', questionsAsked);
            localStorage.setItem('focusSessions', focusSessions);
            localStorage.setItem('flashcardsCreated', flashcardsCreated);
        }

        // Utility Functions
        function clearChat() {
            if (confirm('Clear all messages from this session?')) {
                const chatMessages = document.getElementById('chatMessages');
                // Keep only the welcome message
                const welcomeMessage = chatMessages.firstElementChild;
                chatMessages.innerHTML = '';
                chatMessages.appendChild(welcomeMessage);
            }
        }

        function exportChat() {
            const messages = document.querySelectorAll('.message');
            let chatText = 'PhenBOT Chat Export\\n\\n';
            
            messages.forEach(msg => {
                const content = msg.querySelector('.message-content').textContent;
                const info = msg.querySelector('.message-info').textContent;
                chatText += `${info}\\n${content}\\n\\n`;
            });
            
            const blob = new Blob([chatText], {type: 'text/plain'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `phenbot-chat-${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }

        async function showHistory() {
            try {
                const response = await fetch('/api/chat_history?limit=20');
                const data = await response.json();
                
                if (data.history && data.history.length > 0) {
                    let historyHTML = '<div style="max-height: 400px; overflow-y: auto;">';
                    data.history.forEach(item => {
                        historyHTML += `
                            <div style="border: 1px solid #e1e5e9; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                                <div style="font-weight: 500; color: #667eea; margin-bottom: 0.5rem;">Q: ${item.question}</div>
                                <div style="color: #333; margin-bottom: 0.5rem;">${item.answer}</div>
                                <div style="font-size: 0.8rem; color: #666;">
                                    ${item.timestamp} • ${item.mode} • ${item.length}
                                </div>
                            </div>
                        `;
                    });
                    historyHTML += '</div>';
                    
                    alert('Chat history loaded in console. Check browser console for details.');
                    console.log('Chat History:', data.history);
                } else {
                    alert('No chat history found.');
                }
            } catch (error) {
                alert('Failed to load history: ' + error.message);
            }
        }

        // Flashcards Functions
        function showFlashcards() {
            document.getElementById('flashcardsModal').style.display = 'block';
            loadFlashcardLibrary();
        }

        function closeFlashcards() {
            document.getElementById('flashcardsModal').style.display = 'none';
        }

        function switchTab(tabName) {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
        }

        async function generateFlashcards() {
            const topic = document.getElementById('flashcardTopic').value.trim();
            if (!topic) {
                alert('Please enter a topic for flashcard generation.');
                return;
            }
            
            try {
                const response = await fetch('/api/generate_flashcards', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        source_type: 'topic',
                        topic: topic,
                        subject: document.getElementById('subjectSelect').value,
                        difficulty: document.getElementById('flashcardDifficulty').value,
                        count: parseInt(document.getElementById('flashcardCount').value),
                        save_flashcards: true,
                        title: `${topic} - ${new Date().toLocaleDateString()}`
                    })
                });
                
                const data = await response.json();
                if (response.ok && data.flashcards) {
                    displayGeneratedFlashcards(data.flashcards);
                    flashcardsCreated += data.flashcards.length;
                    updateStats();
                } else {
                    alert('Failed to generate flashcards: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Error generating flashcards: ' + error.message);
            }
        }

        function displayGeneratedFlashcards(flashcards) {
            const container = document.getElementById('generatedFlashcards');
            let html = '<h4>Generated Flashcards:</h4>';
            
            flashcards.forEach((card, index) => {
                html += `
                    <div class="flashcard" onclick="flipCard(this)">
                        <div class="flashcard-content">
                            <div class="front">${card.front}</div>
                            <div class="back" style="display: none;">${card.back}</div>
                        </div>
                        <div class="flashcard-hint">Click to flip</div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }

        function flipCard(cardElement) {
            const front = cardElement.querySelector('.front');
            const back = cardElement.querySelector('.back');
            
            if (front.style.display !== 'none') {
                front.style.display = 'none';
                back.style.display = 'block';
                cardElement.classList.add('flipped');
            } else {
                front.style.display = 'block';
                back.style.display = 'none';
                cardElement.classList.remove('flipped');
            }
        }

        async function loadFlashcardLibrary() {
            try {
                const response = await fetch('/api/get_flashcards');
                const data = await response.json();
                
                const library = document.getElementById('flashcardLibrary');
                if (data.flashcards && data.flashcards.length > 0) {
                    let html = '';
                    data.flashcards.forEach(card => {
                        html += `
                            <div class="flashcard" onclick="flipCard(this)">
                                <div class="flashcard-content">
                                    <div class="front">${card.front}</div>
                                    <div class="back" style="display: none;">${card.back}</div>
                                </div>
                                <div class="flashcard-hint">
                                    ${card.title} • ${card.subject} • ${card.difficulty}
                                </div>
                            </div>
                        `;
                    });
                    library.innerHTML = html;
                } else {
                    library.innerHTML = '<div style="text-align: center; padding: 2rem; color: #666;">No flashcards found. Create some first!</div>';
                }
            } catch (error) {
                document.getElementById('flashcardLibrary').innerHTML = '<div style="text-align: center; padding: 2rem; color: #ef4444;">Error loading flashcards</div>';
            }
        }

        // File-based functions
        async function summarizeFile(fileId) {
            try {
                const response = await fetch('/api/summarize_pdf', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_id: fileId})
                });
                
                const data = await response.json();
                if (response.ok) {
                    addMessage(data.summary, 'bot', {mode: 'summary'});
                } else {
                    alert('Summarization failed: ' + data.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        async function generateFlashcardsFromFile(fileId) {
            try {
                const response = await fetch('/api/generate_flashcards', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        source_type: 'file',
                        file_id: fileId,
                        subject: document.getElementById('subjectSelect').value,
                        difficulty: document.getElementById('flashcardDifficulty').value || 'medium',
                        count: 10,
                        save_flashcards: true,
                        title: `File Flashcards - ${new Date().toLocaleDateString()}`
                    })
                });
                
                const data = await response.json();
                
