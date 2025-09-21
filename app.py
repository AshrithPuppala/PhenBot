# app.py
from flask import Flask, request, jsonify, send_from_directory
import os
import sys
import traceback

app = Flask(__name__, static_folder='static', static_url_path='')

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """
    Initialize Groq client. This function tries to import the Groq SDK
    and initialize the client if GROQ_API_KEY is present. Failures are handled
    gracefully and exposed via GROQ_AVAILABLE / GROQ_ERROR.
    """
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
    """
    Query Groq chat API and return assistant text. If groq client is not available,
    return a friendly message explaining the problem.
    """
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
        # The Groq SDK may expose different methods depending on version.
        # Try the most common call first and otherwise fall back gracefully.
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
            # try to extract response content safely
            if hasattr(response, "choices") and len(response.choices) > 0:
                # SDK object case
                try:
                    return response.choices[0].message.content
                except Exception:
                    pass
            # fallback: dict-like
            try:
                return response['choices'][0]['message']['content']
            except Exception:
                pass

        # second fallback: some SDKs use chat.create
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
            # attempt to extract content
            if isinstance(response, dict):
                return response.get('choices', [{}])[0].get('message', {}).get('content', str(response))
            # if SDK object:
            try:
                return response.choices[0].message.content
            except Exception:
                return str(response)

        # If no known interface found:
        return "Groq client available but SDK interface is not recognised on the server."

    except Exception as e:
        traceback.print_exc()
        return f"Error processing your question: {str(e)}"

# Initialize Groq at startup
print("Starting PhenBOT application...")
initialize_groq()

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"Starting PhenBOT server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
from user_auth import auth, bcrypt, login_manager

login_manager.init_app(app)
bcrypt.init_app(app)
app.register_blueprint(auth)

