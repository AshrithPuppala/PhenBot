# app.py
from flask import Flask, request, jsonify, send_from_directory
import os
import sys
import traceback
import io
from werkzeug.utils import secure_filename
import json
import re
import base64

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

# Store PDF content in memory for this session (Railway-friendly)
pdf_content_store = {}

def initialize_groq():
    """
    Initialize Groq client with better error handling for Railway deployment
    """
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    try:
        from groq import Groq
        print("✓ Groq library imported successfully")
    except ImportError as e:
        GROQ_ERROR = f"Groq library not installed: {e}. Run: pip install groq"
        GROQ_AVAILABLE = False
        print(f"✗ {GROQ_ERROR}")
        return False
    except Exception as e:
        GROQ_ERROR = f"Groq import error: {e}"
        GROQ_AVAILABLE = False
        print(f"✗ {GROQ_ERROR}")
        return False

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY environment variable not set"
        GROQ_AVAILABLE = False
        print(f"✗ {GROQ_ERROR}")
        return False

    try:
        groq_client = Groq(api_key=api_key)
        # Test the connection with a simple call
        test_response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        GROQ_AVAILABLE = True
        GROQ_ERROR = None
        print("✓ Groq client initialized and tested successfully")
        return True
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {e}"
        GROQ_AVAILABLE = False
        print(f"✗ {GROQ_ERROR}")
        return False

def extract_text_from_pdf_fallback(file_content):
    """
    Fallback PDF text extraction without PyPDF2 dependency
    This is a basic approach for Railway deployment
    """
    try:
        # Try to decode as text first (for text-based PDFs)
        text_content = file_content.decode('utf-8', errors='ignore')
        # Remove PDF headers and binary content
        text_content = re.sub(r'%PDF-.*?%%EOF', '', text_content, flags=re.DOTALL)
        # Extract readable text
        lines = []
        for line in text_content.split('\n'):
            line = line.strip()
            # Skip lines that look like PDF commands or binary data
            if (len(line) > 10 and 
                not line.startswith(('%', '<<', '>>', 'obj', 'endobj')) and
                not re.match(r'^[0-9\s<>/]+$', line) and
                any(c.isalpha() for c in line)):
                lines.append(line)
        
        extracted_text = '\n'.join(lines)
        if len(extracted_text.strip()) > 50:  # Must have substantial content
            return extracted_text.strip()
        else:
            return None
    except Exception as e:
        print(f"Fallback PDF extraction failed: {e}")
        return None

def extract_text_from_pdf(file_content):
    """
    Extract text from PDF with multiple fallback methods for Railway
    """
    try:
        # Try PyPDF2 first if available
        try:
            import PyPDF2
            file_stream = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(file_stream)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                return text.strip()
        except ImportError:
            print("PyPDF2 not available, using fallback method")
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
        
        # Fallback method
        fallback_text = extract_text_from_pdf_fallback(file_content)
        if fallback_text:
            return fallback_text
        
        raise Exception("Could not extract readable text from PDF. The file may be image-based or encrypted.")
        
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def get_ai_response(question, subject=None, context=None):
    """
    Query Groq API with better error handling for Railway
    """
    if not groq_client:
        return "AI system is not available. Please check server configuration."

    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Provide step-by-step explanations, use clear examples, and break down complex problems into manageable parts. Always explain the reasoning behind each step.",
        "science": "You are PhenBOT, a science educator. Explain scientific concepts using real-world analogies and examples. Make complex topics accessible and engaging. Connect theories to practical applications.",
        "english": "You are PhenBOT, an English and Literature assistant. Help with grammar, writing techniques, literary analysis, and language concepts. Provide clear explanations and relevant examples.",
        "history": "You are PhenBOT, a history educator. Present historical information through engaging narratives, explain cause and effect relationships, and connect past events to modern contexts.",
        "general": "You are PhenBOT, an advanced AI study companion. Provide clear, accurate, and educational responses across all academic subjects. Adapt your teaching style to make complex topics understandable.",
        "summarize": "You are PhenBOT, an expert at creating comprehensive yet concise summaries. Extract key points, main concepts, and important details while maintaining clarity and educational value.",
        "flashcard": "You are PhenBOT, a flashcard generator. Create educational questions and answers based on the provided content. Focus on key concepts, important facts, and testable material."
    }
    
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    
    # Add context if provided (from uploaded PDF)
    if context:
        # Limit context length to prevent token limit issues
        context = context[:3000] if len(context) > 3000 else context
        system_prompt += f"\n\nUse this context to answer the question:\n{context}"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.9
        )
        
        if hasattr(response, "choices") and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "I received an empty response. Please try rephrasing your question."

    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg:
            return "I'm currently experiencing high demand. Please wait a moment and try again."
        elif "token" in error_msg:
            return "Your question is too long. Please try a shorter question or break it into parts."
        else:
            traceback.print_exc()
            return f"I encountered an error processing your question: {str(e)}"

def generate_flashcards_simple(content, num_cards=10):
    """
    Generate flashcards with simpler parsing for Railway deployment
    """
    if not groq_client or not content:
        return []
    
    # Limit content length to prevent issues
    content = content[:2000] if len(content) > 2000 else content
    
    prompt = f"""Create {min(num_cards, 15)} educational flashcards from this content. 
    Format EXACTLY like this example:
    
    Q: What is photosynthesis?
    A: The process by which plants convert sunlight into energy.
    
    Q: Name the parts of a cell.
    A: Nucleus, cytoplasm, cell membrane, and organelles.
    
    Content: {content}
    
    Create {min(num_cards, 15)} flashcards following the exact Q:/A: format above."""
    
    try:
        response = get_ai_response(prompt, "flashcard")
        flashcards = []
        
        # Parse the response
        lines = response.split('\n')
        current_question = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                current_question = line[2:].strip()
            elif line.startswith('A:') and current_question:
                answer = line[2:].strip()
                flashcards.append({
                    'question': current_question,
                    'answer': answer
                })
                current_question = None
            
            # Stop if we have enough cards
            if len(flashcards) >= num_cards:
                break
        
        return flashcards[:num_cards]
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        # Return sample flashcards as fallback
        return [
            {
                "question": "Based on the uploaded content, what is the main topic?",
                "answer": "Please refer to your uploaded document for specific details."
            }
        ]

# Initialize Groq at startup with better error handling
print("🚀 Starting PhenBOT application...")
try:
    initialize_groq()
    print(f"✓ Initialization complete. Groq available: {GROQ_AVAILABLE}")
except Exception as e:
    print(f"✗ Initialization error: {e}")

@app.route('/')
def serve_index():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        print(f"Error serving index.html: {e}")
        # Fallback HTML if static file not found
        return """
        <!DOCTYPE html>
        <html><head><title>PhenBOT</title></head>
        <body>
        <h1>🤖 PhenBOT</h1>
        <p>Advanced Study Companion</p>
        <p>Static files not found. Please ensure index.html is in the static/ folder.</p>
        <p><a href="/health">Check System Status</a></p>
        </body></html>
        """, 200

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy' if GROQ_AVAILABLE else 'degraded',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'port': os.environ.get('PORT', 'not set'),
        'pdf_support': True,
        'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'local')
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        use_pdf_context = data.get('use_pdf_context', False)

        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400

        if not GROQ_AVAILABLE:
            return jsonify({
                'error': f'AI system not available: {GROQ_ERROR or "Groq not initialized"}'
            }), 500

        # Get PDF context if requested and available
        context = None
        if use_pdf_context and pdf_content_store:
            # Use the most recently uploaded PDF
            latest_pdf = max(pdf_content_store.keys()) if pdf_content_store else None
            if latest_pdf:
                context = pdf_content_store[latest_pdf]

        answer = get_ai_response(question, subject, context)
        return jsonify({
            'answer': answer, 
            'subject': subject, 
            'status': 'success',
            'used_pdf_context': bool(context)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400
        
        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Read file content
        file_content = file.read()
        if len(file_content) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        # Extract text from PDF
        try:
            pdf_text = extract_text_from_pdf(file_content)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        if not pdf_text or len(pdf_text.strip()) < 10:
            return jsonify({'error': 'Could not extract meaningful text from PDF. The file may be image-based, encrypted, or corrupted.'}), 400
        
        # Store PDF content with filename as key
        filename = secure_filename(file.filename)
        pdf_content_store[filename] = pdf_text
        
        return jsonify({
            'status': 'success',
            'message': 'PDF uploaded and processed successfully',
            'filename': filename,
            'text_length': len(pdf_text),
            'preview': pdf_text[:300] + "..." if len(pdf_text) > 300 else pdf_text
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize_content():
    try:
        data = request.get_json()
        source = data.get('source', 'pdf')  # 'pdf' or 'text'
        
        if source == 'pdf':
            if not pdf_content_store:
                return jsonify({'error': 'No PDF uploaded yet'}), 400
            
            # Use the most recently uploaded PDF
            latest_pdf = max(pdf_content_store.keys())
            content = pdf_content_store[latest_pdf]
            
        elif source == 'text':
            content = data.get('text', '').strip()
            if not content:
                return jsonify({'error': 'No text provided for summarization'}), 400
        else:
            return jsonify({'error': 'Invalid source type'}), 400
        
        if not GROQ_AVAILABLE:
            return jsonify({'error': 'AI system not available'}), 500
        
        # Limit content length
        content = content[:4000] if len(content) > 4000 else content
        
        # Generate summary
        summary_prompt = f"Provide a comprehensive summary of the following content. Include key points, main concepts, and important details in a well-structured format:\n\n{content}"
        summary = get_ai_response(summary_prompt, "summarize")
        
        return jsonify({
            'status': 'success',
            'summary': summary,
            'source': source,
            'original_length': len(content),
            'summary_length': len(summary)
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Error generating summary: {str(e)}'}), 500

@app.route('/api/generate-flashcards', methods=['POST'])
def create_flashcards():
    try:
        data = request.get_json()
        source = data.get('source', 'pdf')
        num_cards = min(int(data.get('num_cards', 10)), 15)  # Max 15 cards for Railway
        
        if source == 'pdf':
            if not pdf_content_store:
                return jsonify({'error': 'No PDF uploaded yet'}), 400
            
            latest_pdf = max(pdf_content_store.keys())
            content = pdf_content_store[latest_pdf]
            
        elif source == 'text':
            content = data.get('text', '').strip()
            if not content:
                return jsonify({'error': 'No text provided'}), 400
        else:
            return jsonify({'error': 'Invalid source type'}), 400
        
        if not GROQ_AVAILABLE:
            return jsonify({'error': 'AI system not available'}), 500
        
        # Generate flashcards
        flashcards = generate_flashcards_simple(content, num_cards)
        
        return jsonify({
            'status': 'success',
            'flashcards': flashcards,
            'count': len(flashcards),
            'source': source
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Error generating flashcards: {str(e)}'}), 500

@app.route('/api/pdf-status')
def pdf_status():
    return jsonify({
        'has_pdf': bool(pdf_content_store),
        'pdfs': list(pdf_content_store.keys()),
        'total_pdfs': len(pdf_content_store)
    })

@app.route('/api/test')
def api_test():
    return jsonify({
        'message': 'PhenBOT API is working!',
        'groq_status': GROQ_AVAILABLE,
        'pdf_support': True,
        'environment': 'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local',
        'timestamp': os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'unknown')
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

# Health check for Railway
@app.before_first_request
def startup_check():
    print("🔍 Performing startup health check...")
    print(f"✓ Flask app started")
    print(f"✓ Groq available: {GROQ_AVAILABLE}")
    print(f"✓ Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'Local')}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"🚀 Starting PhenBOT server on port {port} (debug={debug})")
    print(f"📁 Static folder: {app.static_folder}")
    app.run(host='0.0.0.0', port=port, debug=debug)
