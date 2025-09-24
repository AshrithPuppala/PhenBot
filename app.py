import os
import sys
import uuid
import traceback
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import re

from flask import (
    Flask, request, jsonify, render_template, redirect, url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy

# ------------------------
# PDF Processing Setup
# ------------------------
try:
    import PyPDF2
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    PDF_EXTRACTION_AVAILABLE = False
    print("PyPDF2 not available - PDF text extraction disabled")

# Railway deployment fix
if os.environ.get('RAILWAY_ENVIRONMENT'):
    import logging
    logging.basicConfig(level=logging.INFO)

# ------------------------
# Config
# ------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

# App configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", uuid.uuid4().hex)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

# Initialize database
db = SQLAlchemy(app)

# ------------------------
# Models
# ------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class PDFFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(400), nullable=False)
    original_name = db.Column(db.String(400), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class QAHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(50), default="normal")
    length = db.Column(db.String(50), default="normal")
    subject = db.Column(db.String(80), default="general")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Database initialization
def init_database():
    """Initialize database with proper migration handling"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("Database tables created successfully")
            
            # Check if email column exists and add if missing
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'email' not in columns:
                print("Adding email column to user table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE user ADD COLUMN email VARCHAR(150)'))
                    conn.commit()
                print("Email column added successfully")
            
            return True
        except Exception as e:
            print(f"Database initialization error: {e}")
            traceback.print_exc()
            return False

# Initialize database
init_database()

# ------------------------
# Groq initialization
# ------------------------
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

try:
    from groq import Groq
except Exception as e:
    Groq = None
    GROQ_ERROR = "Groq SDK not installed"

def initialize_groq():
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    if Groq is None:
        GROQ_ERROR = GROQ_ERROR or "Groq SDK not available"
        GROQ_AVAILABLE = False
        return False
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY not set"
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

initialize_groq()

# ------------------------
# Helper functions
# ------------------------
def extract_pdf_text(file_path, max_pages=5):
    """Extract text from PDF file"""
    if not PDF_EXTRACTION_AVAILABLE:
        return None
        
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Limit to max_pages to avoid huge prompts
            pages_to_read = min(len(pdf_reader.pages), max_pages)
            
            for page_num in range(pages_to_read):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
            return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return None

def get_system_prompt(mode, length):
    """Get system prompt based on mode and length"""
    base_prompts = {
        "normal": "You are PhenBOT, an advanced AI study companion. Provide clear, helpful responses to educational questions.",
        "analogy": "You are PhenBOT, an AI tutor who explains concepts using creative analogies and real-world comparisons. Always use relatable examples to make complex topics easy to understand.",
        "quiz": "You are PhenBOT in quiz mode. After answering the question, create 2-3 follow-up questions to test the student's understanding of the topic. Format them clearly with numbers.",
        "teach": "You are PhenBOT in teaching mode. Break down complex topics into step-by-step lessons with examples, practice problems, and clear explanations. Use a structured approach.",
        "simple": "You are PhenBOT in simple mode. Explain everything in very simple terms that a beginner can understand. Use basic vocabulary and short sentences."
    }
    
    length_modifiers = {
        "short": " Keep your response concise and to the point, under 100 words.",
        "normal": " Provide a well-balanced response with appropriate detail.",
        "detailed": " Give a comprehensive, detailed explanation with examples and thorough coverage of the topic."
    }
    
    return base_prompts.get(mode, base_prompts["normal"]) + length_modifiers.get(length, length_modifiers["normal"])

def get_enhanced_ai_response(question, mode="normal", length="normal", pdf_context=None):
    """Enhanced AI response with different modes and lengths"""
    if not groq_client or not GROQ_AVAILABLE:
        return "AI system not available on server. Check GROQ_API_KEY and Groq SDK installation."
    
    system_prompt = get_system_prompt(mode, length)
    
    # Add PDF context if available
    if pdf_context:
        system_prompt += f"\n\nThe user has uploaded a PDF: '{pdf_context}'. You can reference this document in your responses when relevant."
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7 if mode != "quiz" else 0.8,
            max_tokens=150 if length == "short" else (300 if length == "normal" else 800),
            top_p=0.9
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        traceback.print_exc()
        return f"Error calling AI: {e}"

def process_pdf_content(text, action, length="normal"):
    """Process PDF content based on the requested action"""
    if not groq_client or not GROQ_AVAILABLE:
        return "AI system not available for PDF processing."
    
    prompts = {
        "summarize": f"Summarize the following PDF content in a {'brief' if length == 'short' else ('comprehensive' if length == 'detailed' else 'clear')} manner:\n\n{text[:3000]}",
        
        "flashcards": f"Create {'5' if length == 'short' else ('15' if length == 'detailed' else '10')} flashcards from this PDF content. Format each as 'Q: [Question] | A: [Answer]':\n\n{text[:3000]}",
        
        "quiz": f"Generate {'3' if length == 'short' else ('8' if length == 'detailed' else '5')} quiz questions with answers from this PDF content. Include multiple choice and short answer questions:\n\n{text[:3000]}",
        
        "outline": f"Create a {'basic' if length == 'short' else ('detailed' if length == 'detailed' else 'structured')} outline of the main topics and subtopics from this PDF:\n\n{text[:3000]}"
    }
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are PhenBOT, an AI study assistant. Process the given PDF content according to the user's request."},
                {"role": "user", "content": prompts[action]}
            ],
            temperature=0.7,
            max_tokens=200 if length == "short" else (400 if length == "normal" else 1000),
            top_p=0.9
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error processing PDF: {e}"

def login_required_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

def login_required_page(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def validate_email(email):
    """Simple email validation"""
    if not email:
        return False
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Check password strength and return score and feedback"""
    if not password:
        return 0, "Password is required"
    
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 25
    else:
        feedback.append("At least 8 characters")
        
    if len(password) >= 12:
        score += 15
        
    if re.search(r'[A-Z]', password):
        score += 20
    else:
        feedback.append("At least one uppercase letter")
        
    if re.search(r'[a-z]', password):
        score += 15
    else:
        feedback.append("At least one lowercase letter")
        
    if re.search(r'[0-9]', password):
        score += 15
    else:
        feedback.append("At least one number")
        
    if re.search(r'[^A-Za-z0-9]', password):
        score += 10
    else:
        feedback.append("At least one special character")
    
    if score < 40:
        return score, "Weak password. " + ", ".join(feedback)
    elif score < 70:
        return score, "Medium strength password"
    else:
        return score, "Strong password"

# ------------------------
# Routes (HTML)
# ------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
                
            username = (data.get("username") or "").strip().lower()
            email = (data.get("email") or "").strip().lower()
            password = data.get("password") or ""
            confirm_password = data.get("confirmPassword") or ""
            
            print(f"Registration attempt: username='{username}', email='{email}'")
            
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters long")
                
            if not email or not validate_email(email):
                errors.append("Please enter a valid email address")
                
            if not password or len(password) < 8:
                errors.append("Password must be at least 8 characters long")
                
            if password != confirm_password:
                errors.append("Passwords do not match")
                
            strength, strength_msg = validate_password_strength(password)
            if strength < 40:
                errors.append("Password is too weak. Please choose a stronger password")
            
            existing_username = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()
            
            if existing_username:
                errors.append("Username already exists")
            if existing_email:
                errors.append("Email already registered")
            
            if errors:
                print(f"Registration errors: {errors}")
                if request.is_json:
                    return jsonify({"success": False, "errors": errors}), 400
                else:
                    for error in errors:
                        flash(error, "danger")
                    return render_template("register.html")
            
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            user = User(username=username, email=email, password_hash=hashed_password)
            
            db.session.add(user)
            db.session.commit()
            
            print(f"User created successfully: id={user.id}, username={user.username}, email={user.email}")
            
            if request.is_json:
                return jsonify({"success": True, "message": "Account created successfully"})
            else:
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for("login"))
                
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            traceback.print_exc()
            error_msg = "An error occurred during registration. Please try again."
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 500
            else:
                flash(error_msg, "danger")
                return render_template("register.html")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
                
            username_or_email = (data.get("username") or "").strip().lower()
            password = data.get("password") or ""
            
            print(f"Login attempt: input='{username_or_email}', password_length={len(password)}")
            
            if not username_or_email or not password:
                error_msg = "Please fill in all fields"
                print("Missing username/email or password")
                if request.is_json:
                    return jsonify({"success": False, "error": error_msg}), 400
                else:
                    flash(error_msg, "danger")
                    return render_template("login.html")
            
            user = None
            
            if validate_email(username_or_email):
                print(f"Input looks like email, searching by email: {username_or_email}")
                user = User.query.filter(User.email == username_or_email).first()
                if user:
                    print(f"Found user by email: {user.username}")
            
            if not user:
                print(f"Searching by username: {username_or_email}")
                user = User.query.filter(User.username == username_or_email).first()
                if user:
                    print(f"Found user by username: {user.username}")
            
            if not user:
                print("User not found in database")
                error_msg = "Invalid username/email or password"
                if request.is_json:
                    return jsonify({"success": False, "error": error_msg}), 400
                else:
                    flash(error_msg, "danger")
                    return render_template("login.html")
            
            print(f"Verifying password for user: {user.username}")
            
            password_valid = check_password_hash(user.password_hash, password)
            print(f"Password verification result: {password_valid}")
            
            if password_valid:
                print("Login successful, setting session")
                session.clear()
                session["user_id"] = user.id
                session["username"] = user.username
                session["email"] = user.email or ""
                session.permanent = True
                
                print(f"Session set: user_id={session.get('user_id')}, username={session.get('username')}")
                
                if request.is_json:
                    return jsonify({
                        "success": True, 
                        "message": "Login successful",
                        "redirect": url_for("dashboard")
                    })
                else:
                    flash("Login successful!", "success")
                    return redirect(url_for("dashboard"))
            else:
                print("Password verification failed")
                error_msg = "Invalid username/email or password"
                if request.is_json:
                    return jsonify({"success": False, "error": error_msg}), 400
                else:
                    flash(error_msg, "danger")
                    return render_template("login.html")
                    
        except Exception as e:
            print(f"Login error: {e}")
            traceback.print_exc()
            error_msg = "An error occurred during login. Please try again."
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 500
            else:
                flash(error_msg, "danger")
                return render_template("login.html")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    print(f"Logging out user: {session.get('username')}")
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required_page
def dashboard():
    print(f"Dashboard accessed by user: {session.get('username')} (ID: {session.get('user_id')})")
    return render_template("dashboard.html", username=session.get("username"))

# ------------------------
# API endpoints
# ------------------------
@app.route("/api/chat", methods=["POST"])
@login_required_json
def api_chat():
    """API chat endpoint - wrapper for the main chat function"""
    return chat()
    try:
        data = request.get_json() or {}
        message = (data.get("message") or "").strip()
        mode = data.get("mode", "normal")
        length = data.get("length", "normal")
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        print(f"Chat: user_id={session.get('user_id')}, mode={mode}, length={length}, message_preview={message[:50]}...")
        
        # Check if GROQ is available
        if not GROQ_AVAILABLE:
            return jsonify({"error": f"AI service not available: {GROQ_ERROR}"}), 503
        
        # Get AI response using the existing function
        response = get_enhanced_ai_response(message, mode, length)
        
        # Save to history
        try:
            hist = QAHistory(
                user_id=session["user_id"], 
                question=message, 
                answer=response, 
                mode=mode,
                length=length,
                subject="chat"
            )
            db.session.add(hist)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving chat history: {e}")
        
        return jsonify({
            "success": True,
            "response": response,
            "mode": mode,
            "length": length
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Chat error: {str(e)}"}), 500
@app.route("/api/enhanced-chat", methods=["POST"])
@login_required_json
def api_enhanced_chat():
    """Enhanced chat endpoint with modes and length options"""
    try:
        data = request.get_json() or {}
        message = (data.get("message") or "").strip()
        mode = data.get("mode", "normal")
        length = data.get("length", "normal")
        pdf_context = data.get("pdf_context")
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        print(f"Enhanced chat: user_id={session.get('user_id')}, mode={mode}, length={length}")
        
        response = get_enhanced_ai_response(message, mode, length, pdf_context)
        
        # Save to history
        try:
            hist = QAHistory(
                user_id=session["user_id"], 
                question=message, 
                answer=response, 
                mode=mode,
                length=length,
                subject="general"
            )
            db.session.add(hist)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving chat history: {e}")
        
        return jsonify({
            "success": True,
            "response": response,
            "mode": mode,
            "length": length,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Enhanced chat error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Chat error: {str(e)}"}), 500

@app.route("/api/process-pdf", methods=["POST"])
@login_required_json
def api_process_pdf():
    """Process PDF with different actions using actual PDF content"""
    try:
        data = request.get_json() or {}
        filename = data.get("filename", "").strip()
        action = data.get("action", "").strip()
        length = data.get("length", "normal")
        
        if not filename or not action:
            return jsonify({"error": "Filename and action required"}), 400
            
        # Find PDF by original_name
        pdf_record = PDFFile.query.filter_by(
            user_id=session["user_id"], 
            original_name=filename
        ).first()
        
        if not pdf_record:
            return jsonify({"error": "PDF not found in your uploads"}), 404
            
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_record.filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "PDF file not found on disk"}), 404
            
        if not GROQ_AVAILABLE:
            return jsonify({"error": f"AI service not available: {GROQ_ERROR}"}), 503
        
        # Try to extract PDF text
        pdf_text = extract_pdf_text(file_path) if PDF_EXTRACTION_AVAILABLE else None
        
        # Create prompts based on action and available text
        if pdf_text:
            prompts = {
                "summarize": f"Please summarize the following PDF content from '{pdf_record.original_name}':\n\n{pdf_text[:3000]}{'...' if len(pdf_text) > 3000 else ''}",
                "flashcards": f"Create flashcards based on the content from '{pdf_record.original_name}'. Format each as 'Q: [Question]\\nA: [Answer]\\n\\n'. Here's the content:\n\n{pdf_text[:2500]}{'...' if len(pdf_text) > 2500 else ''}",
                "quiz": f"Create quiz questions (multiple choice and short answer) based on '{pdf_record.original_name}'. Here's the content:\n\n{pdf_text[:2500]}{'...' if len(pdf_text) > 2500 else ''}",
                "outline": f"Create a structured outline based on the content from '{pdf_record.original_name}':\n\n{pdf_text[:2500]}{'...' if len(pdf_text) > 2500 else ''}"
            }
        else:
            prompts = {
                "summarize": f"I can help summarize '{pdf_record.original_name}', but I need you to share the key content first. Please paste the main sections or tell me what topics the PDF covers.",
                "flashcards": f"I'll create flashcards for '{pdf_record.original_name}'. Please share the main concepts, definitions, or key points, and I'll format them as:\n\nQ: [Question]\nA: [Answer]",
                "quiz": f"I can create quiz questions for '{pdf_record.original_name}'. Please share the main topics or content, and I'll create various types of questions.",
                "outline": f"I'll help create an outline for '{pdf_record.original_name}'. Please share the main sections or topics from the document."
            }
        
        prompt = prompts.get(action, "Invalid action specified")
        
        if length == "short":
            prompt += "\n\nPlease keep the response concise."
        elif length == "detailed":
            prompt += "\n\nPlease provide a detailed, comprehensive response."
        
        if pdf_text:
            response = process_pdf_content(pdf_text, action, length)
        else:
            response = get_enhanced_ai_response(prompt, "normal", length)
        
        try:
            hist = QAHistory(
                user_id=session["user_id"], 
                question=f"PDF {action}: {pdf_record.original_name}", 
                answer=response, 
                mode=f"pdf_{action}",
                length=length,
                subject=f"pdf_{action}"
            )
            db.session.add(hist)
            db.session.commit()
        except Exception as e:
            print(f"Failed to save PDF processing to history: {e}")
            db.session.rollback()
        
        return jsonify({
            "success": True,
            "result": response,
            "action": action,
            "filename": pdf_record.original_name,
            "text_extracted": pdf_text is not None
        })
        
    except Exception as e:
        print(f"PDF processing error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

# File upload endpoints
ALLOWED_EXT = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/api/upload-pdf", methods=["POST"])
@login_required_json
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    files = request.files.getlist("file")  # Handle multiple files
    if not files or files[0].filename == "":
        return jsonify({"error": "No files selected"}), 400
    
    uploaded_files = []
    errors = []
    
    try:
        for file in files:
            if not allowed_file(file.filename):
                errors.append(f"{file.filename}: Only PDF files allowed")
                continue
                
            original = secure_filename(file.filename)
            unique = f"{session['user_id']}_{uuid.uuid4().hex}_{original}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
            file.save(save_path)
            
            rec = PDFFile(user_id=session["user_id"], filename=unique, original_name=original)
            db.session.add(rec)
            db.session.commit()
            
            url = url_for("static", filename=f"uploads/{unique}")
            
            uploaded_files.append({
                "filename": original,
                "unique_filename": unique,
                "file_id": rec.id,
                "url": url
            })
        
        if uploaded_files:
            return jsonify({
                "success": True,
                "message": f"{len(uploaded_files)} PDF(s) uploaded successfully",
                "files": uploaded_files,
                "errors": errors
            }), 201
        else:
            return jsonify({"error": "No valid PDF files uploaded", "errors": errors}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500
@app.route("/api/pdfs", methods=["GET"])
@login_required_json
def list_pdfs():
    try:
        uid = session["user_id"]
        files = PDFFile.query.filter_by(user_id=uid).order_by(PDFFile.uploaded_at.desc()).all()
        out = []
        for p in files:
            out.append({
                "id": p.id, 
                "name": p.original_name, 
                "url": url_for("static", filename=f"uploads/{p.filename}"), 
                "uploaded_at": p.uploaded_at.isoformat()
            })
        return jsonify({"files": out})
    except Exception as e:
        print(f"List PDFs error: {e}")
        return jsonify({"error": "Failed to list PDFs"}), 500

@app.route("/api/history", methods=["GET"])
@login_required_json
def get_history():
    try:
        uid = session["user_id"]
        rows = QAHistory.query.filter_by(user_id=uid).order_by(QAHistory.created_at.desc()).limit(50).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id, 
                "question": r.question, 
                "answer": r.answer, 
                "mode": getattr(r, 'mode', 'normal'),
                "length": getattr(r, 'length', 'normal'),
                "subject": r.subject, 
                "created_at": r.created_at.isoformat()
            })
        return jsonify({"history": out})
    except Exception as e:
        print(f"Get history error: {e}")
        return jsonify({"error": "Failed to get history"}), 500
@app.route("/api/delete-pdf/<int:file_id>", methods=["DELETE"])
@login_required_json
def delete_pdf(file_id):
    try:
        pdf_file = PDFFile.query.filter_by(id=file_id, user_id=session["user_id"]).first()
        
        if not pdf_file:
            return jsonify({"error": "PDF not found"}), 404
        
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file from disk: {file_path}")
        
        db.session.delete(pdf_file)
        db.session.commit()
        
        print(f"Deleted PDF: {pdf_file.original_name} (ID: {file_id})")
        
        return jsonify({
            "success": True,
            "message": f"PDF '{pdf_file.original_name}' deleted successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to delete PDF: {str(e)}"}), 500
# Health check
@app.route("/health")
def health():
    try:
        return jsonify({
            "status": "ok",
            "groq_available": GROQ_AVAILABLE,
            "pdf_extraction_available": PDF_EXTRACTION_AVAILABLE,
            "api_key_present": bool(os.environ.get("GROQ_API_KEY")),
            "error": GROQ_ERROR,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "database_path": app.config["SQLALCHEMY_DATABASE_URI"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Debug routes (remove in production)
@app.route("/debug/users")
def debug_users():
    """Debug route to see all users in database"""
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "password_hash": user.password_hash[:50] + "...",
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            "users": user_list, 
            "count": len(user_list),
            "database_path": app.config["SQLALCHEMY_DATABASE_URI"]
        })
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/debug/session")
def debug_session():
    """Debug route to check session data"""
    return jsonify({
        "session_data": dict(session),
        "session_keys": list(session.keys()),
        "user_logged_in": "user_id" in session
    })

# Error handlers
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    flash("Page not found", "error")
    return redirect(url_for("login"))

@app.errorhandler(500)
def handle_500(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    flash("An error occurred", "error")
    return redirect(url_for("login"))

@app.errorhandler(413)
def handle_413(e):
    return jsonify({"error": "File too large. Maximum size is 32MB."}), 413

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting PhenBOT on port {port} (debug={debug})")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Groq AI available: {GROQ_AVAILABLE}")
    print(f"PDF extraction available: {PDF_EXTRACTION_AVAILABLE}")
    if not GROQ_AVAILABLE:
        print(f"Groq error: {GROQ_ERROR}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)





