# app.py
from flask import Flask, request, jsonify, send_from_directory, abort
import os
import sys
import traceback
import json
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', static_url_path='')

# ---------- Groq/AI setup (unchanged) ----------
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

def get_ai_response(question, subject=None):
    if not groq_client:
        return "AI system is not available. Please check the server configuration."

    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations, use clear examples, and break down complex problems into manageable parts. Always explain the reasoning behind each step.",
        "science": "You are PhenBOT, a science educator. Explain scientific concepts using real-world analogies and examples. Make complex topics accessible and engaging. Connect theories to practical applications.",
        "english": "You are PhenBOT, an English and Literature assistant. Help with grammar, writing techniques, literary analysis, and language concepts. Provide clear explanations and relevant examples.",
        "history": "You are PhenBOT, a history educator. Present historical information through engaging narratives, explain cause and effect relationships, and connect past events to modern contexts.",
        "general": "You are PhenBOT, an advanced AI study companion. Provide clear, accurate, and educational responses across all academic subjects. Adapt your teaching style to make complex topics understandable."
    }
    system_prompt = system_prompts.get(subject, system_prompts["general"])

    try:
        if hasattr(groq_client, 'chat') and hasattr(groq_client.chat, 'completions'):
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
            if hasattr(response, "choices") and len(response.choices) > 0:
                try:
                    return response.choices[0].message.content
                except Exception:
                    pass
            try:
                return response['choices'][0]['message']['content']
            except Exception:
                pass

        if hasattr(groq_client, 'chat') and hasattr(groq_client.chat, 'create'):
            response = groq_client.chat.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=600
            )
            if isinstance(response, dict):
                return response.get('choices', [{}])[0].get('message', {}).get('content', str(response))
            try:
                return response.choices[0].message.content
            except Exception:
                return str(response)

        return "Groq client available but SDK interface is not recognised on the server."

    except Exception as e:
        traceback.print_exc()
        return f"Error processing your question: {str(e)}"

# Initialize Groq at startup
print("Starting PhenBOT application...")
initialize_groq()

# ---------- Uploads and Flashcards setup ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
FLASHCARDS_FILE = os.path.join(BASE_DIR, 'flashcards.json')

os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_flashcards():
    try:
        if not os.path.exists(FLASHCARDS_FILE):
            return []
        with open(FLASHCARDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_flashcards(cards):
    with open(FLASHCARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

# ensure flashcards file exists
if not os.path.exists(FLASHCARDS_FILE):
    save_flashcards([])

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Routes ----------
@app.route('/')
def serve_index():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        print(f"Error serving index.html: {e}")
        return f"Error loading application. Please check if index.html exists in the static folder. Error: {str(e)}", 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'port': os.environ.get('PORT', 'not set')
    })

# Chat endpoint (unchanged)
@app.route('/api/ask', methods=['POST'])
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
            return jsonify({
                'error': f'AI system not available: {GROQ_ERROR or "Groq not initialized"}'
            }), 500

        answer = get_ai_response(question, subject)
        return jsonify({'answer': answer, 'subject': subject, 'status': 'success'})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/test')
def api_test():
    return jsonify({
        'message': 'PhenBOT API is working!',
        'groq_status': GROQ_AVAILABLE,
        'timestamp': os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'unknown')
    })

# ---------- PDF upload & listing ----------
@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """
    Accept a single file field named 'file' (multipart/form-data).
    Saves file to static/uploads and returns the public path.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Make unique to avoid collisions
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(UPLOAD_DIR, unique_name)
        file.save(save_path)
        public_url = f"/static/uploads/{unique_name}"
        return jsonify({'message': 'Uploaded', 'url': public_url}), 201
    else:
        return jsonify({'error': 'Invalid file type (only PDF allowed)'}), 400

@app.route('/api/pdfs', methods=['GET'])
def list_pdfs():
    files = []
    for fname in sorted(os.listdir(UPLOAD_DIR), reverse=True):
        if allowed_file(fname):
            files.append({
                'name': fname,
                'url': f"/static/uploads/{fname}"
            })
    return jsonify({'files': files})

# ---------- Flashcards API ----------
@app.route('/api/flashcards', methods=['GET', 'POST'])
def flashcards_collection():
    if request.method == 'GET':
        cards = load_flashcards()
        return jsonify({'flashcards': cards})

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        if not question or not answer:
            return jsonify({'error': 'Both question and answer are required'}), 400
        cards = load_flashcards()
        card = {
            'id': uuid.uuid4().hex,
            'question': question,
            'answer': answer
        }
        cards.insert(0, card)  # newest first
        save_flashcards(cards)
        return jsonify({'flashcard': card}), 201

@app.route('/api/flashcards/<card_id>', methods=['DELETE'])
def flashcard_delete(card_id):
    cards = load_flashcards()
    new = [c for c in cards if c.get('id') != card_id]
    if len(new) == len(cards):
        return jsonify({'error': 'Card not found'}), 404
    save_flashcards(new)
    return jsonify({'message': 'Deleted'}), 200

# ---------- Error handlers ----------
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ---------- Start ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"Starting PhenBOT server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
