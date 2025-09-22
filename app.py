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
# Config
# ------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

# IMPORTANT: set SECRET_KEY in env while deploying. Fallback to random for dev.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", uuid.uuid4().hex)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

db = SQLAlchemy(app)

# ------------------------
# Models
# ------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)  # Added email field
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PDFFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(400), nullable=False)       # stored filename
    original_name = db.Column(db.String(400), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class QAHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(80), default="general")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create DB - FIXED: Handle existing database properly
with app.app_context():
    # Check if we need to add the email column to existing database
    try:
        # Try to query for email column - if it fails, we need to add it
        db.engine.execute('SELECT email FROM user LIMIT 1')
    except Exception as e:
        print("Adding email column to existing database...")
        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN email VARCHAR(150)')
            print("Email column added successfully")
        except Exception as alter_error:
            print(f"Could not add email column: {alter_error}")
    
    # Create all tables (will create new ones and skip existing ones)
    db.create_all()
    print("Database initialized successfully")

# ------------------------
# Groq initialization (safe)
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
        # Do NOT pass 'proxies' or unsupported kwargs.
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        return True
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {e}"
        GROQ_AVAILABLE = False
        return False

# Try to initialize; doesn't crash app if missing
initialize_groq()

def get_ai_response(question, subject="general"):
    if not groq_client or not GROQ_AVAILABLE:
        return "AI system not available on server. Check GROQ_API_KEY and Groq SDK installation."
    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations.",
        "science": "You are PhenBOT, a science educator. Explain concepts with analogies.",
        "english": "You are PhenBOT, an English tutor. Help with grammar and writing.",
        "history": "You are PhenBOT, a history educator. Explain context and causes.",
        "general": "You are PhenBOT, an advanced study companion."
    }
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    try:
        # Try common SDK interfaces safely
        if hasattr(groq_client, "chat") and hasattr(groq_client.chat, "completions"):
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
                    return response["choices"][0]["message"]["content"]
                except Exception:
                    return str(response)
        if hasattr(groq_client, "chat") and hasattr(groq_client.chat, "create"):
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
        return "Groq client interface not recognized"
    except Exception as e:
        traceback.print_exc()
        return f"Error calling Groq: {e}"

# ------------------------
# Helpers / auth
# ------------------------
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
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
            
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        confirm_password = data.get("confirmPassword") or ""
        
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
            
        # Check password strength
        strength, strength_msg = validate_password_strength(password)
        if strength < 40:
            errors.append("Password is too weak. Please choose a stronger password")
        
        # Check if user exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                errors.append("Username already exists")
            if existing_user.email == email:
                errors.append("Email already registered")
        
        if errors:
            if request.is_json:
                return jsonify({"success": False, "errors": errors}), 400
            else:
                for error in errors:
                    flash(error, "danger")
                return render_template("register.html")
        
        # Create user
        try:
            hashed = generate_password_hash(password)
            user = User(username=username, email=email, password_hash=hashed)
            db.session.add(user)
            db.session.commit()
            
            print(f"User created successfully: username={username}, email={email}")
            
            if request.is_json:
                return jsonify({"success": True, "message": "Account created successfully"})
            else:
                flash("Account created! Please log in.", "success")
                return redirect(url_for("login"))
                
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {e}")
            error_msg = "An error occurred during registration"
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
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
            
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        
        print(f"Login attempt: username/email={username}")
        
        if not username or not password:
            error_msg = "Please fill in all fields"
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 400
            else:
                flash(error_msg, "danger")
                return render_template("login.html")
        
        # FIXED: Search for user by username OR email
        user = None
        
        # Check if username is actually an email
        if validate_email(username):
            print("Searching by email...")
            user = User.query.filter_by(email=username).first()
        else:
            print("Searching by username...")
            user = User.query.filter_by(username=username).first()
        
        # ADDITIONAL FIX: If not found by the initial method, try the other way
        if not user:
            print("User not found by initial method, trying alternative...")
            if validate_email(username):
                # If we searched by email and didn't find, try username
                user = User.query.filter_by(username=username).first()
            else:
                # If we searched by username and didn't find, try email
                user = User.query.filter_by(email=username).first()
        
        if user:
            print(f"User found: id={user.id}, username={user.username}, email={user.email}")
            
            # FIXED: Check password hash properly
            if check_password_hash(user.password_hash, password):
                print("Password verified successfully")
                session["user_id"] = user.id
                session["username"] = user.username
                session["email"] = user.email or ""
                
                if request.is_json:
                    return jsonify({"success": True, "message": "Login successful"})
                else:
                    flash("Logged in successfully!", "success")
                    return redirect(url_for("dashboard"))
            else:
                print("Password verification failed")
                error_msg = "Invalid username/email or password"
        else:
            print("User not found in database")
            error_msg = "Invalid username/email or password"
            
        # If we reach here, login failed
        if request.is_json:
            return jsonify({"success": False, "error": error_msg}), 400
        else:
            flash(error_msg, "danger")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required_page
def dashboard():
    # Renders the SPA/dashboard template (client will call /api/* endpoints)
    return render_template("dashboard.html", username=session.get("username"))

# ------------------------
# Debug route to check users in database
# ------------------------
@app.route("/debug/users")
def debug_users():
    """Debug route to see all users in database - REMOVE IN PRODUCTION"""
    if not app.debug:
        return "Not available in production", 404
    
    users = User.query.all()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash[:20] + "...",  # Only show first 20 chars for security
            "created_at": user.created_at.isoformat()
        })
    
    return jsonify({"users": user_list, "count": len(user_list)})

# ------------------------
# Health & system info
# ------------------------
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "groq_available": GROQ_AVAILABLE,
        "api_key_present": bool(os.environ.get("GROQ_API_KEY")),
        "error": GROQ_ERROR,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    })

# ------------------------
# API endpoints
# ------------------------
@app.route("/api/ask", methods=["POST"])
@login_required_json
def api_ask():
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    subject = data.get("subject", "general")
    if not question:
        return jsonify({"error": "Question required"}), 400
    if not GROQ_AVAILABLE:
        return jsonify({"error": f"AI not available: {GROQ_ERROR or 'Groq not initialized'}"}), 503
    answer = get_ai_response(question, subject)
    try:
        hist = QAHistory(user_id=session["user_id"], question=question, answer=answer, subject=subject)
        db.session.add(hist)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({"answer": answer})

# Enhanced chat endpoint for the dashboard
@app.route("/api/chat", methods=["POST"])
@login_required_json
def api_chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message required"}), 400
    
    if GROQ_AVAILABLE:
        response = get_ai_response(message, "general")
    else:
        response = f"I received your message: '{message}'. AI service is currently unavailable, but I'm here to help! Try asking about study tips, time management, or general academic questions."
    
    try:
        hist = QAHistory(user_id=session["user_id"], question=message, answer=response, subject="general")
        db.session.add(hist)
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    return jsonify({
        "response": response,
        "timestamp": datetime.now().isoformat()
    })

# PDF upload
ALLOWED_EXT = {"pdf"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/api/upload-pdf", methods=["POST"])
@login_required_json
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Only .pdf allowed"}), 400
    original = secure_filename(f.filename)
    unique = f"{session['user_id']}_{uuid.uuid4().hex}_{original}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
    f.save(save_path)
    rec = PDFFile(user_id=session["user_id"], filename=unique, original_name=original)
    db.session.add(rec)
    db.session.commit()
    url = url_for("static", filename=f"uploads/{unique}")
    return jsonify({"message": "Uploaded successfully", "filename": original, "url": url}), 201

# Enhanced upload endpoint for dashboard
@app.route("/api/upload", methods=["POST"])
@login_required_json
def api_upload():
    """Handle file uploads from dashboard"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        original = secure_filename(file.filename)
        unique = f"{session['user_id']}_{uuid.uuid4().hex}_{original}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
        file.save(save_path)
        
        rec = PDFFile(user_id=session["user_id"], filename=unique, original_name=original)
        db.session.add(rec)
        db.session.commit()
        
        url = url_for("static", filename=f"uploads/{unique}")
        return jsonify({
            "success": True,
            "filename": original,
            "message": "File uploaded successfully",
            "url": url
        })
    
    return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

@app.route("/api/pdfs", methods=["GET"])
@login_required_json
def list_pdfs():
    uid = session["user_id"]
    files = PDFFile.query.filter_by(user_id=uid).order_by(PDFFile.uploaded_at.desc()).all()
    out = [{"id": p.id, "name": p.original_name, "url": url_for("static", filename=f"uploads/{p.filename}"), "uploaded_at": p.uploaded_at.isoformat()} for p in files]
    return jsonify({"files": out})

@app.route("/api/history", methods=["GET"])
@login_required_json
def get_history():
    uid = session["user_id"]
    rows = QAHistory.query.filter_by(user_id=uid).order_by(QAHistory.created_at.desc()).limit(50).all()
    out = [{"id": r.id, "question": r.question, "answer": r.answer, "subject": r.subject, "created_at": r.created_at.isoformat()} for r in rows]
    return jsonify({"history": out})

# ------------------------
# Error handlers
# ------------------------
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    return render_template("404.html"), 404

@app.errorhandler(500)
def handle_500(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("500.html"), 500

# ------------------------
# Run (dev)
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting PhenBOT on port {port} (debug={debug})")
    print(f"Groq AI available: {GROQ_AVAILABLE}")
    if not GROQ_AVAILABLE:
        print(f"Groq error: {GROQ_ERROR}")
    app.run(host="0.0.0.0", port=port, debug=debug)
