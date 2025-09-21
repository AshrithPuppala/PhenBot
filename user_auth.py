import json, os
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()
login_manager = LoginManager()

USERS_FILE = 'users.json'

# Load users from JSON
def load_users():
    if not os.path.exists(USERS_FILE):
        return {"users": []}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

# Save users to JSON
def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# User class
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    data = load_users()
    for u in data['users']:
        if str(u['id']) == str(user_id):
            return User(u['id'], u['username'], u['email'], u['password_hash'])
    return None

# Signup route
@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = data['password']

    all_users = load_users()
    if any(u['email'] == email for u in all_users['users']):
        return jsonify({'error': 'Email already exists'}), 400

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = {
        "id": len(all_users['users']) + 1,
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "streak": 0,
        "history": []
    }
    all_users['users'].append(new_user)
    save_users(all_users)

    return jsonify({'success': True})

# Login route
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    all_users = load_users()
    user_data = next((u for u in all_users['users'] if u['email'] == email), None)
    if not user_data or not bcrypt.check_password_hash(user_data['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 400

    user = User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'])
    login_user(user)
    return jsonify({'success': True, 'username': user.username})

# Logout
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})
