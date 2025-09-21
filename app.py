from flask import Flask, request, jsonify, send_from_directory
import os
import sys

app = Flask(__name__, static_folder='static', static_url_path='')

# Global variables for Groq client
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initialize Groq client with proper error handling"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    print("Initializing Groq client...")
    
    try:
        from groq import Groq
        print("Groq library imported successfully")
        
        api_key = os.environ.get("GROQ_API_KEY")
        print(f"API key present: {bool(api_key)}")
        
        if not api_key:
            GROQ_ERROR = "GROQ_API_KEY environment variable not set"
            print(f"Error: {GROQ_ERROR}")
            return False
        
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
        return True
        
    except ImportError as e:
        GROQ_ERROR = f"Groq library not available: {str(e)}"
        print(f"Import Error: {GROQ_ERROR}")
        return False
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {str(e)}"
        print(f"Error: {GROQ_ERROR}")
        return False

def get_ai_response(question, subject=None):
    """Get response from Groq API"""
    if not groq_client:
        return "AI system is not available. Please check the server configuration."
    
    # Subject-specific system prompts
    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations, use clear examples, and break down complex problems into manageable parts. Always explain the reasoning behind each step.",
        "science": "You are PhenBOT, a science educator. Explain scientific concepts using real-world analogies and examples. Make complex topics accessible and engaging. Connect theories to practical applications.",
        "english": "You are PhenBOT, an English and Literature assistant. Help with grammar, writing techniques, literary analysis, and language concepts. Provide clear explanations and relevant examples.",
        "history": "You are PhenBOT, a history educator. Present historical information through engaging narratives, explain cause and effect relationships, and connect past events to modern contexts.",
        "general": "You are PhenBOT, an advanced AI study companion. Provide clear, accurate, and educational responses across all academic subjects. Adapt your teaching style to make complex topics understandable."
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
            max_tokens=600,
            top_p=0.9
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}"
        print(f"API Error: {error_msg}")
        return error_msg

# Initialize Groq on startup
print("Starting PhenBOT application...")
initialize_groq()

@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        print(f"Error serving index.html: {e}")
        return f"Error loading application. Please check if index.html exists in the static folder. Error: {str(e)}", 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
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
    """Handle study questions"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        print(f"Processing question: {question[:50]}... (Subject: {subject})")
        
        # Check if Groq is available
        if not GROQ_AVAILABLE:
            return jsonify({
                'error': f'AI system not available: {GROQ_ERROR}'
            }), 500
        
        # Get AI response
        answer = get_ai_response(question, subject)
        
        return jsonify({
            'answer': answer,
            'subject': subject,
            'status': 'success'
        })
        
    except Exception as e:
        error_msg = f'Server error: {str(e)}'
        print(f"API Error: {error_msg}")
        return jsonify({'error': error_msg}), 500

@app.route('/api/test')
def api_test():
    """Test endpoint"""
    return jsonify({
        'message': 'PhenBOT API is working!',
        'groq_status': GROQ_AVAILABLE,
        'timestamp': os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'unknown')
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting PhenBOT server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Groq available: {GROQ_AVAILABLE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
