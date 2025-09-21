from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_bcrypt import Bcrypt
import os
import sys

# --- Flask setup ---
app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get("SECRET_KEY", "phenbot_secret_key")

# --- Auth setup ---
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

# --- In-memory user store (for demo; use persistent db for production) ---
USERS = {}

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
        self.data = USERS.get(username, {})

@login_manager.user_loader
def load_user(username):
    if username in USERS:
        return User(username)
    return None

# -------------------- Groq AI SETUP ---------------------
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

def get_ai_response(question, subject=None, username=None):
    if not groq_client:
        return "AI system is not available. Please check the server configuration."
    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations, use clear examples, and break down complex problems into manageable parts. Always explain the reasoning behind each step.",
        "science": "You are PhenBOT, a science educator. Explain scientific concepts using real-world analogies and examples. Make complex topics accessible and engaging. Connect theories to practical applications.",
        "english": "You are PhenBOT, an English and Literature assistant. Help with grammar, writing techniques, literary analysis, and language concepts. Provide clear explanations and relevant examples.",
        "history": "You are PhenBOT, a history educator. Present historical information through engaging narratives, explain cause and effect relationships, and connect past events to modern contexts.",
        "general": "You are PhenBOT, an advanced AI study companion. Provide clear, accurate, and educational responses across all academic subjects. Adapt your teaching style to make complex topics understandable.",
    }
    # Personalize the greeting if a username is present.
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    if username:
        system_prompt += f"\nPersonalize responses for the student '{username}'."
    try:
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
        return response.choices[0].message.content
    except Exception as e:
        return f"Error from Groq: {str(e)}"

initialize_groq()

# ------- REGISTRATION & LOGIN ROUTES -----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password or username in USERS:
            return jsonify({"error": "Invalid or duplicate username"}), 400
        hashpw = bcrypt.generate_password_hash(password).decode('utf-8')
        USERS[username] = {"password": hashpw}
        return jsonify({"success": True})
    return send_from_directory(app.static_folder, "login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        username = data.get("username", "").strip()
        password = data.get("password", "")
        user = USERS.get(username)
        if not user or not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401
        login_user(User(username))
        return jsonify({"success": True})
    return send_from_directory(app.static_folder, "login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# -------------- MAIN APP AND PROTECTED API -----------

@app.route("/")
@login_required
def serve_main_ui():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/ask", methods=["POST"])
@login_required
def api_ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'AI system not available: {GROQ_ERROR or "Groq not initialized"}'}), 500
        answer = get_ai_response(question, subject, current_user.username)
        return jsonify({'answer': answer, 'subject': subject, 'status': 'success'})
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route("/health")
def health_check():
    return jsonify({
        'status': 'healthy' if GROQ_AVAILABLE else 'unhealthy',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'port': os.environ.get('PORT', 'not set')
    })

# ---- DEFAULT STATIC SEND FILE ROUTE for /static assets ---
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# --------------- ERROR HANDLING -------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
