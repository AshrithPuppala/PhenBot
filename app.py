# Enhanced PhenBOT Flask Backend with AI Modes, PDF Processing, and Flashcards

import os
import sys
import uuid
import json
import traceback
from functools import wraps
from datetime import datetime
import PyPDF2
import io
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

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", uuid.uuid4().hex)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

db = SQLAlchemy(app)

# ------------------------
# Enhanced Models
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
    file_size = db.Column(db.Integer, nullable=True)
    page_count = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)

class QAHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(50), default="normal")
    response_length = db.Column(db.String(20), default="normal")
    subject = db.Column(db.String(80), default="general")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    difficulty = db.Column(db.String(20), default="medium")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    times_reviewed = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # 'pomodoro', 'flashcard', 'chat'
    duration_minutes = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Database initialization
def init_database():
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
            return True
        except Exception as e:
            print(f"Database initialization error: {e}")
            traceback.print_exc()
            return False

init_database()

# ------------------------
# Enhanced Groq AI with Multiple Modes
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

def get_ai_response(question, mode="normal", response_length="normal", subject="general"):
    """Enhanced AI response with different modes and length controls"""
    if not groq_client or not GROQ_AVAILABLE:
        return "AI system not available. Check GROQ_API_KEY and Groq SDK installation."
    
    # Define system prompts for different modes
    mode_prompts = {
        "normal": "You are PhenBOT, an intelligent study companion. Provide helpful, accurate responses.",
        "analogy": "You are PhenBOT in analogy mode. Explain concepts using clear, relatable analogies and metaphors. Always include at least one analogy in your response.",
        "quiz": "You are PhenBOT in quiz mode. Create engaging quiz questions based on the topic. Ask follow-up questions to test understanding.",
        "teach": "You are PhenBOT in teaching mode. Provide step-by-step explanations, breaking down complex concepts into digestible parts. Use examples and check for understanding.",
        "socratic": "You are PhenBOT using the Socratic method. Guide learning through thoughtful questions rather than direct answers. Help students discover answers themselves.",
        "explain": "You are PhenBOT in ELI5 (Explain Like I'm 5) mode. Use simple language and everyday examples to explain complex concepts clearly."
    }
    
    # Subject-specific additions
    subject_additions = {
        "math": " Focus on mathematical concepts and provide clear problem-solving steps.",
        "science": " Emphasize scientific principles and real-world applications.",
        "english": " Help with language, literature, writing, and communication skills.",
        "history": " Explain historical context, causes, and effects of events.",
        "general": " Cover any academic subject as needed."
    }
    
    # Length instructions
    length_instructions = {
        "short": " Keep responses concise and to the point (2-3 sentences max).",
        "normal": " Provide balanced, informative responses (1-2 paragraphs).",
        "detailed": " Give comprehensive, thorough explanations with examples and context."
    }
    
    system_prompt = (mode_prompts.get(mode, mode_prompts["normal"]) + 
                    subject_additions.get(subject, subject_additions["general"]) +
                    length_instructions.get(response_length, length_instructions["normal"]))
    
    # Adjust max tokens based on response length
    max_tokens = {
        "short": 150,
        "normal": 500,
        "detailed": 800
    }.get(response_length, 500)
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=max_tokens,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        traceback.print_exc()
        return f"Error calling AI: {e}"

def extract_text_from_pdf(file_path):
    """Extract text content from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return None

def summarize_pdf_content(text, length="normal"):
    """Summarize PDF content using AI"""
    if not text or not GROQ_AVAILABLE:
        return "Unable to summarize PDF content."
    
    # Truncate text if too long (API limits)
    max_chars = 8000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    
    length_instructions = {
        "short": "Provide a brief summary in 2-3 sentences.",
        "normal": "Provide a comprehensive summary in 1-2 paragraphs.",
        "detailed": "Provide a detailed summary with key points and main concepts."
    }
    
    prompt = f"""Summarize the following document content. {length_instructions.get(length, length_instructions['normal'])}

Document content:
{text}

Summary:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error summarizing PDF: {e}"

def create_flashcards_from_text(text, count=10, difficulty="medium"):
    """Generate flashcards from PDF text using AI"""
    if not text or not GROQ_AVAILABLE:
        return []
    
    # Truncate text if too long
    max_chars = 6000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    
    difficulty_instructions = {
        "easy": "Create basic, fundamental questions suitable for beginners.",
        "medium": "Create intermediate-level questions that require understanding of concepts.",
        "hard": "Create advanced questions that require deep analysis and critical thinking."
    }
    
    prompt = f"""Based on the following document, create {count} flashcards for studying. {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}

Format each flashcard as:
FRONT: [Question or term]
BACK: [Answer or definition]

Document content:
{text}

Flashcards:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800
        )
        
        # Parse the response to extract flashcards
        flashcards = []
        lines = response.choices[0].message.content.split('\n')
        current_front = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('FRONT:'):
                current_front = line[6:].strip()
            elif line.startswith('BACK:') and current_front:
                back = line[5:].strip()
                flashcards.append({'front': current_front, 'back': back})
                current_front = None
        
        return flashcards
    except Exception as e:
        print(f"Error creating flashcards: {e}")
        return []

def generate_topic_flashcards(topic, count=10, difficulty="medium"):
    """Generate flashcards for a specific topic using AI"""
    if not GROQ_AVAILABLE:
        return []
    
    difficulty_instructions = {
        "easy": "Create basic, fundamental questions suitable for beginners.",
        "medium": "Create intermediate-level questions that require understanding of concepts.",
        "hard": "Create advanced questions that require deep analysis and critical thinking."
    }
    
    prompt = f"""Create {count} educational flashcards about "{topic}". {difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}

Format each flashcard as:
FRONT: [Question or term]
BACK: [Answer or definition]

Make sure the flashcards cover different aspects of the topic and are educational and accurate.

Flashcards:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800
        )
        
        # Parse the response to extract flashcards
        flashcards = []
        lines = response.choices[0].message.content.split('\n')
        current_front = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('FRONT:'):
                current_front = line[6:].strip()
            elif line.startswith('BACK:') and current_front:
                back = line[5:].strip()
                flashcards.append({'front': current_front, 'back': back})
                current_front = None
        
        return flashcards
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

# ------------------------
# Helper functions
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
# Routes (keeping existing ones and adding new ones)
# ------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required_page
def dashboard():
    print(f"Dashboard accessed by user: {session.get('username')} (ID: {session.get('user_id')})")
    # Use the enhanced dashboard template
    return render_template("dashboard.html", username=session.get("username"))
