import os
import sys
import uuid
import traceback
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask, request, jsonify, send_from_directory,
    render_template, redirect, url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy
# --------------------
# Config & folders
# --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', uuid.uuid4().hex)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max
db = SQLAlchemy(app)
# --------------------
# Models
# --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class PDFFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(300), nullable=False)          # stored filename
    original_name = db.Column(db.String(300), nullable=False)     # uploaded original
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class QAHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(80), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# Create DB tables
with app.app_context():
    db.create_all()
# --------------------
# Groq (AI) init - don't crash app if missing
# --------------------
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None
def initialize_groq():
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    try:
        from groq import Groq
    except Exception as e:
        GROQ_ERROR = f"Groq library not available: {e}"
        GROQ_AVAILABLE = False
        return False
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY environment variable not set"
        GROQ_AVAILABLE = False
        return False
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        return True
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {e}"
        GROQ_AVAILABLE = False
        return False
# initialize at startup (safe)
initialize_groq()
def get_ai_response(question, subject='general'):
    if not groq_client:
        return "AI system not available on server. Check GROQ_API_KEY and Groq SDK installation."
    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations and clear examples.",
        "science": "You are PhenBOT, a science educator. Explain using analogies and examples.",
        "english": "You are PhenBOT, an English & literature assistant. Be clear and constructive.",
        "history": "You are PhenBOT, a history educator. Explain context and cause-effect.",
        "general": "You are PhenBOT, an advanced study companion."
    }
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    try:
        # try the common SDK method variants
        if hasattr(groq_client, 'chat') and hasattr(groq_client.chat, 'completions'):
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=600,
                top_p=0.9
            )
            try:
                return response.choices[0].message.content
            except Exception:
                try:
                    return response['choices'][0]['message']['content']
                except Exception:
                    return str(response)
        if hasattr(groq_client, 'chat') and hasattr(groq_client.chat, 'create'):
            response = groq_client.chat.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=600
            )
            try:
                return response.choices[0].message.content
            except Exception:
                return str(response)
        return "Groq client interface not recognized."
    except Exception as e:
        traceback.print_exc()
        return f"Error fetching AI response: {str(e)}"
# --------------------
# Auth decorators
# --------------------
def login_required_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated
def login_required_page(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated
# --------------------
# HTML routes (login/register + SPA entry)
# --------------------
@app.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('app_ui'))
    return render_template('index.html')
@app.route('/app')
@login_required_page
def app_ui():
    # serve SPA index (static)
    return send_from_directory(app.static_folder, 'index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        if not username or not password:
            flash('Username and password required', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))
    # This is the correct line to render the register.html template
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # API login for the SPA
        if request.is_json:
            data = request.get_json() or {}
            username = data.get('username')
            password = data.get('password')
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        # Form-based login for the login.html page
        else:
            username = (request.form.get('username') or '').strip()
            password = (request.form.get('password') or '').strip()
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Logged in successfully', 'success')
                return redirect(url_for('app_ui'))
            flash('Invalid credentials', 'danger')
    # This is the correct line to render the login.html template
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('root'))
# --------------------
# API endpoints
# --------------------
@app.route('/api/me')
@login_required_json
def api_me():
    uid = session['user_id']
    user = User.query.get(uid)
    return jsonify({'id': user.id, 'username': user.username})
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    })
# AI ask - save QA history
@app.route('/api/ask', methods=['POST'])
@login_required_json
def api_ask():
    data = request.get_json() or {}
    question = (data.get('question') or '').strip()
    subject = data.get('subject', 'general')
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    if not GROQ_AVAILABLE:
        return jsonify({'error': f'AI not available: {GROQ_ERROR or "Groq not initialized"}'}), 503
    answer = get_ai_response(question, subject)
    # save to history
    try:
        history = QAHistory(user_id=session['user_id'], question=question, answer=answer, subject=subject)
        db.session.add(history)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({'answer': answer, 'subject': subject})
# QA history retrieval
@app.route('/api/history', methods=['GET'])
@login_required_json
def api_history():
    uid = session['user_id']
    rows = QAHistory.query.filter_by(user_id=uid).order_by(QAHistory.created_at.desc()).limit(50).all()
    out = [{'id': r.id, 'question': r.question, 'answer': r.answer, 'subject': r.subject, 'created_at': r.created_at.isoformat()} for r in rows]
    return jsonify({'history': out})
# --------------------
# PDF upload/list (per-user)
# --------------------
ALLOWED_EXT = {'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT
@app.route('/api/upload-pdf', methods=['POST'])
@login_required_json
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'Only PDF allowed (extension .pdf)'}), 400
    original = secure_filename(f.filename)
    # store with uid prefix for safety / separation
    unique_name = f"{session['user_id']}_{uuid.uuid4().hex}_{original}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    f.save(save_path)
    pdf = PDFFile(user_id=session['user_id'], filename=unique_name, original_name=original)
    db.session.add(pdf)
    db.session.commit()
    url = url_for('static', filename=f"uploads/{unique_name}")
    return jsonify({'message': 'Uploaded', 'url': url}), 201
@app.route('/api/pdfs', methods=['GET'])
@login_required_json
def list_pdfs():
    uid = session['user_id']
    files = PDFFile.query.filter_by(user_id=uid).order_by(PDFFile.uploaded_at.desc()).all()
    out = [{'id': p.id, 'name': p.original_name, 'url': url_for('static', filename=f"uploads/{p.filename}"), 'uploaded_at': p.uploaded_at.isoformat()} for p in files]
    return jsonify({'files': out})
# --------------------
# Flashcards (per-user)
# --------------------
@app.route('/api/flashcards', methods=['GET', 'POST'])
@login_required_json
def flashcards_collection():
    uid = session['user_id']
    if request.method == 'GET':
        cards = Flashcard.query.filter_by(user_id=uid).order_by(Flashcard.created_at.desc()).all()
        out = [{'id': c.id, 'question': c.question, 'answer': c.answer} for c in cards]
        return jsonify({'flashcards': out})
    data = request.get_json() or {}
    q = (data.get('question') or '').strip()
    a = (data.get('answer') or '').strip()
    if not q or not a:
        return jsonify({'error': 'Question and answer required'}), 400
    card = Flashcard(user_id=uid, question=q, answer=a)
    db.session.add(card)
    db.session.commit()
    return jsonify({'flashcard': {'id': card.id, 'question': q, 'answer': a}}), 201
@app.route('/api/flashcards/<int:card_id>', methods=['DELETE'])
@login_required_json
def flashcard_delete(card_id):
    uid = session['user_id']
    card = Flashcard.query.filter_by(id=card_id, user_id=uid).first()
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    db.session.delete(card)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200
# --------------------
# Bookmarks (per-user)
# --------------------
@app.route('/api/bookmarks', methods=['GET', 'POST'])
@login_required_json
def bookmarks_collection():
    uid = session['user_id']
    if request.method == 'GET':
        items = Bookmark.query.filter_by(user_id=uid).order_by(Bookmark.created_at.desc()).all()
        out = [{'id': b.id, 'title': b.title, 'url': b.url} for b in items]
        return jsonify({'bookmarks': out})
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    url = (data.get('url') or '').strip()
    if not title or not url:
        return jsonify({'error': 'Title and URL required'}), 400
    bm = Bookmark(user_id=uid, title=title, url=url)
    db.session.add(bm)
    db.session.commit()
    return jsonify({'bookmark': {'id': bm.id, 'title': bm.title, 'url': bm.url}}), 201
@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@login_required_json
def bookmark_delete(bookmark_id):
    uid = session['user_id']
    bm = Bookmark.query.filter_by(id=bookmark_id, user_id=uid).first()
    if not bm:
        return jsonify({'error': 'Bookmark not found'}), 404
    db.session.delete(bm)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200
# --------------------
# Fallback 404 -> SPA (when logged in)
# --------------------
@app.errorhandler(404)
def page_not_found(e):
    if 'user_id' in session:
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except Exception:
            pass
    return jsonify({'error': 'Not found'}), 404
# --------------------
# Run
# --------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"Starting PhenBOT server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
