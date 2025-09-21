from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///phenbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Groq client initialization
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initialize Groq client with proper error handling"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    try:
        from groq import Groq
        print("Groq library imported successfully")
        
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            GROQ_ERROR = "GROQ_API_KEY environment variable not set"
            print(f"Error: {GROQ_ERROR}")
            return False
        
        # Initialize with minimal parameters to avoid 'proxies' error
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
        return True
        
    except ImportError as e:
        GROQ_ERROR = f"Groq library not available: {str(e)}"
        print(f"Import Error: {GROQ_ERROR}")
        return False
    except TypeError as e:
        if "'proxies'" in str(e):
            # Handle the proxies parameter error
            try:
                # Try alternative initialization without extra parameters
                from groq import Groq
                groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
                GROQ_AVAILABLE = True
                print("Groq client initialized successfully (alternative method)")
                return True
            except Exception as e2:
                GROQ_ERROR = f"Groq initialization failed: {str(e2)}"
                print(f"Alternative init failed: {GROQ_ERROR}")
                return False
        else:
            GROQ_ERROR = f"Groq initialization failed: {str(e)}"
            print(f"Type Error: {GROQ_ERROR}")
            return False
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {str(e)}"
        print(f"General Error: {GROQ_ERROR}")
        return False

def get_ai_response(question, subject=None):
    """Get response from Groq API"""
    if not groq_client:
        return "AI system is not available. Please check the server configuration."
    
    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations with clear examples.",
        "science": "You are PhenBOT, a science educator. Explain concepts using real-world analogies.",
        "english": "You are PhenBOT, an English tutor. Help with grammar, writing, and literature analysis.",
        "history": "You are PhenBOT, a history educator. Present information through engaging narratives.",
        "general": "You are PhenBOT, an AI study companion. Provide clear, educational responses."
    }
    
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error processing your question: {str(e)}"

# Initialize database and Groq
with app.app_context():
    db.create_all()
    initialize_groq()

# Routes
@app.route('/')
def root():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('app_ui'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('app_ui'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('root'))

@app.route('/app')
def app_ui():
    """Main application UI"""
    if 'user_id' not in session:
        flash('Please log in to access the application', 'error')
        return redirect(url_for('login'))
    
    return render_template('app.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'users_count': User.query.count()
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """Handle study questions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        if not GROQ_AVAILABLE:
            return jsonify({
                'error': f'AI system not available: {GROQ_ERROR}'
            }), 500
        
        answer = get_ai_response(question, subject)
        
        return jsonify({
            'answer': answer,
            'subject': subject,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting PhenBOT server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Groq available: {GROQ_AVAILABLE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
