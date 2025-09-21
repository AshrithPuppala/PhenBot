# app.py
from flask import Flask, request, jsonify, send_from_directory
import os
import sys
import traceback
import PyPDF2
import io
from werkzeug.utils import secure_filename
import json

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

# Store PDF content in memory for this session
pdf_content_store = {}

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

def extract_text_from_pdf(file_stream):
    """Extract text content from PDF file stream"""
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def get_ai_response(question, subject=None, context=None):
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
        "general": "You are PhenBOT, an advanced AI study companion. Provide clear, accurate, and educational responses across all academic subjects. Adapt your teaching style to make complex topics understandable.",
        "summarize": "You are PhenBOT, an expert at creating comprehensive yet concise summaries. Extract key points, main concepts, and important details while maintaining clarity and educational value.",
        "flashcard": "You are PhenBOT, a flashcard generator. Create educational questions and answers based on the provided content. Focus on key concepts, important facts, and testable material."
    }
    
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    
    # Add context if provided (from uploaded PDF)
    if context:
        system_prompt += f"\n\nUse this context to answer the question: {context[:2000]}..."  # Limit context length

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

def generate_flashcards(content, num_cards=10):
    """Generate flashcards from content using AI"""
    if not groq_client or not content:
        return []
    
    prompt = f"""Create {num_cards} educational flashcards from the following content. 
    Format each flashcard as JSON with 'question' and 'answer' fields.
    Focus on key concepts, important facts, definitions, and testable material.
    Make questions clear and answers concise but complete.
    
    Content: {content[:3000]}
    
    Return only a JSON array of flashcards."""
    
    try:
        response = get_ai_response(prompt, "flashcard")
        # Try to extract JSON from response
        if response.startswith('['):
            flashcards = json.loads(response)
            return flashcards[:num_cards]  # Limit to requested number
        else:
            # Fallback: parse manually if AI didn't return pure JSON
            lines = response.split('\n')
            flashcards = []
            current_card = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Q:') or line.startswith('Question:'):
                    if current_card:
                        flashcards.append(current_card)
                    current_card = {'question': line.split(':', 1)[1].strip()}
                elif line.startswith('A:') or line.startswith('Answer:'):
                    if 'question' in current_card:
                        current_card['answer'] = line.split(':', 1)[1].strip()
            
            if current_card and 'question' in current_card and 'answer' in current_card:
                flashcards.append(current_card)
            
            return flashcards[:num_cards]
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

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
        'port': os.environ.get('PORT', 'not set'),
        'pdf_support': True
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
        
        # Extract text from PDF
        file_stream = io.BytesIO(file.read())
        pdf_text = extract_text_from_pdf(file_stream)
        
        if not pdf_text.strip():
            return jsonify({'error': 'Could not extract text from PDF. The file may be image-based or corrupted.'}), 400
        
        # Store PDF content with filename as key
        filename = secure_filename(file.filename)
        pdf_content_store[filename] = pdf_text
        
        return jsonify({
            'status': 'success',
            'message': 'PDF uploaded and processed successfully',
            'filename': filename,
            'text_length': len(pdf_text),
            'preview': pdf_text[:200] + "..." if len(pdf_text) > 200 else pdf_text
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
        
        # Generate summary
        summary_prompt = f"Provide a comprehensive summary of the following content. Include key points, main concepts, and important details in a well-structured format:\n\n{content[:4000]}"
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
        num_cards = min(int(data.get('num_cards', 10)), 20)  # Max 20 cards
        
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
        flashcards = generate_flashcards(content, num_cards)
        
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
        'timestamp': os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'unknown')
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"Starting PhenBOT server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
