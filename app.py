# app.py
from flask import Flask, request, jsonify, send_from_directory
import os, sys, traceback

app = Flask(__name__, static_folder='static', static_url_path='')

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """
    Initialize Groq client without unsupported parameters.
    """
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    try:
        from groq import Groq
    except Exception as e:
        GROQ_ERROR = f"Groq library not installed: {e}"
        GROQ_AVAILABLE = False
        return False

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY environment variable not set"
        GROQ_AVAILABLE = False
        return False

    try:
        # The current Groq SDK does not take 'proxies' or other kwargs
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        return True
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {e}"
        GROQ_AVAILABLE = False
        return False

def get_ai_response(question, subject="general"):
    """
    Query Groq chat API and return response.
    """
    if not groq_client:
        return "AI system is not available. Please check server configuration."

    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations with clear examples.",
        "science": "You are PhenBOT, a science educator. Explain concepts using analogies and practical examples.",
        "english": "You are PhenBOT, an English assistant. Help with grammar, writing, and literary analysis.",
        "history": "You are PhenBOT, a history educator. Provide engaging narratives and explain cause/effect.",
        "general": "You are PhenBOT, an AI study companion. Provide clear and educational responses."
    }
    system_prompt = system_prompts.get(subject, system_prompts["general"])

    try:
        # Groq SDK v2+ interface
        if hasattr(groq_client, 'chat'):
            chat_attr = getattr(groq_client, 'chat')
            # Try completions first
            if hasattr(chat_attr, 'completions'):
                response = chat_attr.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.7,
                    max_tokens=600,
                    top_p=0.9
                )
                try:
                    return response.choices[0].message.content
                except Exception:
                    return str(response)
            # fallback: chat.create
            elif hasattr(chat_attr, 'create'):
                response = chat_attr.create(
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
        return "Groq client available but SDK interface is not recognized."
    except Exception as e:
        traceback.print_exc()
        return f"Error processing your question: {str(e)}"

# Initialize Groq at startup
print("Starting PhenBOT server...")
initialize_groq()

# ----------------- Routes -----------------
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

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
            return jsonify({'error': f'AI system not available: {GROQ_ERROR or "Groq not initialized"}'}), 500

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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Run server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"Server running on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
