from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import sys

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # Use env var

USERS_FILE = "users.json"

# Ensure users.json exists and is a valid JSON dict
def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    else:
        # If file exists but is invalid, reset
        try:
            with open(USERS_FILE, "r") as f:
                json.load(f)
        except Exception:
            with open(USERS_FILE, "w") as f:
                json.dump({}, f)

# ----------------------------
# Helpers
# ----------------------------
def load_users():
    ensure_users_file()
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_users_file()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()
        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    ensure_users_file()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()
        if username in users:
            return render_template("register.html", error="Username already exists")
        users[username] = password
        save_users(users)
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    })

# ----------------------------
# Error Pages
# ----------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    ensure_users_file()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
