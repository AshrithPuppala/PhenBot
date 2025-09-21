import json
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directories
USERS_FILE = os.path.join(BASE_DIR, 'data/users.json')
FLASHCARDS_DIR = os.path.join(BASE_DIR, 'data/flashcards')
HISTORY_DIR = os.path.join(BASE_DIR, 'data/history')
UPLOAD_DIR = os.path.join(BASE_DIR, 'data/uploads')

os.makedirs(FLASHCARDS_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- USER AUTH ----------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def register_user(email, secret_code):
    users = load_users()
    if any(u['email'] == email for u in users):
        return False, "Email already registered"
    hashed_code = generate_password_hash(secret_code)
    users.append({"email": email, "secret_code": hashed_code})
    save_users(users)
    return True, "Registration successful"

def authenticate_user(email, secret_code):
    users = load_users()
    user = next((u for u in users if u['email'] == email), None)
    if user and check_password_hash(user['secret_code'], secret_code):
        return user
    return None

# ---------------- FLASHCARDS ----------------
def get_flashcards_file(email):
    return os.path.join(FLASHCARDS_DIR, f"{email}.json")

def load_flashcards(email):
    file_path = get_flashcards_file(email)
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f)

def save_flashcards(email, flashcards):
    file_path = get_flashcards_file(email)
    with open(file_path, 'w') as f:
        json.dump(flashcards, f, indent=2)

def create_flashcard(email, question, answer, subject):
    flashcards = load_flashcards(email)
    flashcards.append({
        "id": str(uuid.uuid4()),
        "question": question,
        "answer": answer,
        "subject": subject
    })
    save_flashcards(email, flashcards)

# ---------------- HISTORY ----------------
def get_history_file(email):
    return os.path.join(HISTORY_DIR, f"{email}.json")

def load_history(email):
    file_path = get_history_file(email)
    if not os.path.exists(file_path):
        return {"questions_asked": 0, "concepts_learned": 0, "study_time": 0}
    with open(file_path, 'r') as f:
        return json.load(f)

def save_history(email, data):
    file_path = get_history_file(email)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def update_history(email, questions_asked=0, concepts_learned=0, study_time=0):
    history = load_history(email)
    history["questions_asked"] += questions_asked
    history["concepts_learned"] += concepts_learned
    history["study_time"] += study_time
    save_history(email, history)

# ---------------- FILE UPLOAD ----------------
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_pdf(file, email):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        user_folder = os.path.join(UPLOAD_DIR, email)
        os.makedirs(user_folder, exist_ok=True)
        file_path = os.path.join(user_folder, filename)
        file.save(file_path)
        return file_path
    return None
