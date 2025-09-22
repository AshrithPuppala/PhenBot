import os
import json
import traceback
from functools import wraps
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from flask_bcrypt import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# --- User helpers ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def logged_in():
    return "username" in session

def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not logged_in():
            return jsonify({"error": "Authentication required"}), 401
        return func(*args, **kwargs)
    return wrapper

# --- Groq Setup ---
try:
    from groq import Groq
except ImportError:
    Groq = None
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    if Groq is None:
        GROQ_ERROR = "Groq SDK not installed"
        GROQ_AVAILABLE = False
        return
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY env missing"
        GROQ_AVAILABLE = False
        return
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
    except Exception as e:
        GROQ_ERROR = str(e)
        GROQ_AVAILABLE = False

initialize_groq()

def get_ai_response(question, subject):
    if not groq_client or not GROQ_AVAILABLE:
        return "AI system unavailable"
    prompts = {
        "math": "You are a math tutor. Explain clearly.",
        "science": "You are a science tutor. Explain clearly.",
        "english": "You are an English tutor. Explain clearly.",
        "history": "You are a history tutor. Explain clearly.",
        "general": "You are a smart assistant.",
    }
    prompt = prompts.get(subject, prompts["general"])
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-instant",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return f"Error calling Groq API: {e}"

# --- Routes ---

@app.route("/")
def index():
    if logged_in():
        return send_from_directory(app.static_folder, "index.html")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if logged_in():
        return redirect(url_for("index"))
    if request.method == "POST":
        data = request.form or request.get_json(force=True, silent=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")
        users = load_users()
        stored_hash = users.get(username)
        if stored_hash and check_password_hash(stored_hash, password):
            session["username"] = username
            return redirect(url_for("index"))
        return "Invalid credentials", 401
    return send_from_directory(app.static_folder, "login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if logged_in():
        return redirect(url_for("index"))
    if request.method == "POST":
        data = request.form or request.get_json(force=True, silent=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password or len(password) < 4:
            return "Invalid username or password", 400
        users = load_users()
        if username in users:
            return "User already exists", 400
        hashpw = generate_password_hash(password).decode("utf-8")
        users[username] = hashpw
        save_users(users)
        return redirect(url_for("login"))
    return send_from_directory(app.static_folder, "register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect(url_for("login"))
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/ask", methods=["POST"])
@require_login
def api_ask():
    try:
        data = request.get_json(force=True, silent=True)
        question = data.get("question", "").strip()
        subject = data.get("subject", "general")
        if question == "":
            return jsonify({"error": "Empty question"}), 400
        if not GROQ_AVAILABLE:
            return jsonify({"error": f"AI system unavailable: {GROQ_ERROR}"}), 503
        answer = get_ai_response(question, subject)
        return jsonify({"answer": answer})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Server error: {e}"}), 500

@app.route("/health")
def health():
    return jsonify({
        "healthy": True,
        "groq_available": GROQ_AVAILABLE,
        "error": GROQ_ERROR
    })

@app.route("/static/<path:path>")
def static_files(path):
    static_path = os.path.join(app.static_folder, path)
    if not os.path.exists(static_path):
        return jsonify({"error": "Static file not found"}), 404
    return send_from_directory(app.static_folder, path)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
