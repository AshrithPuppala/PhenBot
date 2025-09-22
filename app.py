import os
import sys
import uuid
import traceback
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

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

# Create DB
with app.app_context():
    db.create_all()

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
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password or len(password) < 4:
            flash("Invalid username or password (min 4 chars)", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for("register"))
        hashed = generate_password_hash(password)
        user = User(username=username, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Logged in", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required_page
def dashboard():
    # Renders the SPA/dashboard template (client will call /api/* endpoints)
    return render_template("dashboard.html", username=session.get("username"))

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
    return jsonify({"message": "Uploaded", "url": url}), 201

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
    return render_template("404.html"), 404

@app.errorhandler(500)
def handle_500(e):
    return render_template("500.html"), 500

# ------------------------
# Run (dev)
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
