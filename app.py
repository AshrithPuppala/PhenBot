from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import sys
import json
import traceback

app = Flask(__name__, static_folder='static')
app.secret_key = "supersecretkey"  # CHANGE in production!

USERS_FILE = "users.json"

# ----------------------------
# User Management
# ----------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
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

# ----------------------------
# Health Check API (for AI system)
# ----------------------------
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    })

# ----------------------------
# Error Handlers
# ----------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html", error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway gives PORT
    app.run(host="0.0.0.0", port=port)


