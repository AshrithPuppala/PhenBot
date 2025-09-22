from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import openai
import json
import os
from datetime import datetime
import PyPDF2
import io
import uuid
import speech_recognition as sr
from gtts import gTTS
import tempfile
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///phenbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)

# Set OpenAI API key (you'll need to get this from OpenAI)
openai.api_key = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key-here')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(50), default='normal')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PDFDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(200))
    difficulty = db.Column(db.String(50), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# AI Chat Mode Prompts
CHAT_MODES = {
    'normal': {
        'system_prompt': "You are PhenBot, an advanced AI study companion. Provide helpful, accurate, and educational responses to help students learn effectively.",
        'style': "conversational and supportive"
    },
    'analogy': {
        'system_prompt': "You are PhenBot in Analogy Mode. Explain complex concepts using creative analogies and metaphors to make them easier to understand. Always start with 'Think of it like this:' and use relatable comparisons.",
        'style': "analogy-focused and creative"
    },
    'quiz': {
        'system_prompt': "You are PhenBot in Quiz Mode. Ask engaging questions to test the user's knowledge, then provide immediate feedback. Format questions clearly and explain answers thoroughly.",
        'style': "interactive questioning"
    },
    'teach': {
        'system_prompt': "You are PhenBot in Teaching Mode. Break down complex topics into step-by-step explanations. Use structured learning approaches with clear examples and practice exercises.",
        'style': "structured and educational"
    },
    'socratic': {
        'system_prompt': "You are PhenBot in Socratic Mode. Guide learning through thoughtful questions that help users discover answers themselves. Ask follow-up questions to deepen understanding.",
        'style': "questioning and guiding"
    },
    'explain': {
        'system_prompt': "You are PhenBot in ELI5 Mode. Explain everything in simple terms that a 5-year-old could understand. Use everyday language, avoid jargon, and include fun examples.",
        'style': "simple and accessible"
    }
}

RESPONSE_LENGTHS = {
    'short': "Keep responses concise and to the point, under 100 words.",
    'normal': "Provide moderate detail in responses, around 150-300 words.",
    'detailed': "Give comprehensive, detailed explanations with examples, 300+ words."
}

def get_ai_response(message, mode='normal', length='normal', context=""):
    """Generate AI response based on mode and length preferences"""
    try:
        mode_config = CHAT_MODES.get(mode, CHAT_MODES['normal'])
        length_instruction = RESPONSE_LENGTHS.get(length, RESPONSE_LENGTHS['normal'])
        
        system_message = f"{mode_config['system_prompt']} {length_instruction}"
        
        if context:
            system_message += f"\n\nContext from uploaded PDF: {context[:1000]}..."
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            max_tokens=500 if length == 'short' else (800 if length == 'normal' else 1200),
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        app.logger.error(f"OpenAI API error: {str(e)}")
        return "I'm having trouble connecting to my AI brain right now. Please try again in a moment!"

def extract_text_from_pdf(file_stream):
    """Extract text content from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        app.logger.error(f"PDF extraction error: {str(e)}")
        return None

def generate_flashcards_from_content(content, topic="", difficulty="medium", count=10):
    """Generate flashcards from PDF content or topic using AI"""
    try:
        if content:
            prompt = f"Create {count} educational flashcards from this content. Format as JSON with 'question' and 'answer' fields:\n\n{content[:2000]}"
        else:
            prompt = f"Create {count} {difficulty} level flashcards about {topic}. Format as JSON with 'question' and 'answer' fields."
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational content creator. Create clear, concise flashcards that help students learn effectively. Return only valid JSON array."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.5
        )
        
        flashcards_text = response.choices[0].message.content.strip()
        # Try to extract JSON from response
        if flashcards_text.startswith('```json'):
            flashcards_text = flashcards_text.split('```json')[1].split('```')[0]
        elif flashcards_text.startswith('```'):
            flashcards_text = flashcards_text.split('```')[1]
            
        flashcards = json.loads(flashcards_text)
        return flashcards if isinstance(flashcards, list) else [flashcards]
    
    except Exception as e:
        app.logger.error(f"Flashcard generation error: {str(e)}")
        return []

def summarize_pdf_content(content, length='normal'):
    """Generate summary of PDF content"""
    try:
        length_map = {
            'short': "Provide a brief summary in 2-3 sentences.",
            'normal': "Provide a comprehensive summary in 1-2 paragraphs.",
            'detailed': "Provide a detailed summary with key points and main topics covered."
        }
        
        prompt = f"Summarize this document content. {length_map.get(length, length_map['normal'])}:\n\n{content[:3000]}"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a document summarization expert. Create clear, informative summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        app.logger.error(f"Summarization error: {str(e)}")
        return "Unable to generate summary at this time."

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', username=user.username if user else 'Student')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials!'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists!'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered!'})
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful!'})
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    mode = data.get('mode', 'normal')
    length = data.get('length', 'normal')
    pdf_context = data.get('context', '')
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Generate AI response
        ai_response = get_ai_response(message, mode, length, pdf_context)
        
        # Save to chat history
        chat_record = ChatHistory(
            user_id=session['user_id'],
            message=message,
            response=ai_response,
            mode=mode
        )
        db.session.add(chat_record)
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'mode': mode,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Failed to generate response'}), 500

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Please upload a valid PDF file'}), 400
    
    try:
        # Extract text from PDF
        file_stream = io.BytesIO(file.read())
        text_content = extract_text_from_pdf(file_stream)
        
        if not text_content:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Save file info to database
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Reset file stream and save file
        file.stream.seek(0)
        file.save(file_path)
        
        pdf_doc = PDFDocument(
            user_id=session['user_id'],
            filename=filename,
            file_path=file_path,
            content=text_content
        )
        db.session.add(pdf_doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file_id': pdf_doc.id,
            'filename': filename,
            'message': 'PDF uploaded successfully!'
        })
    
    except Exception as e:
        app.logger.error(f"PDF upload error: {str(e)}")
        return jsonify({'error': 'Failed to process PDF'}), 500

@app.route('/api/summarize-pdf/<int:pdf_id>')
def summarize_pdf(pdf_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    length = request.args.get('length', 'normal')
    
    pdf_doc = PDFDocument.query.filter_by(id=pdf_id, user_id=session['user_id']).first()
    if not pdf_doc:
        return jsonify({'error': 'PDF not found'}), 404
    
    try:
        summary = summarize_pdf_content(pdf_doc.content, length)
        return jsonify({
            'summary': summary,
            'filename': pdf_doc.filename
        })
    
    except Exception as e:
        app.logger.error(f"PDF summarization error: {str(e)}")
        return jsonify({'error': 'Failed to generate summary'}), 500

@app.route('/api/create-flashcards', methods=['POST'])
def create_flashcards():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    source_type = data.get('source', 'manual')  # manual, pdf, or topic
    
    try:
        if source_type == 'manual':
            # Manual flashcard creation
            question = data.get('question', '').strip()
            answer = data.get('answer', '').strip()
            topic = data.get('topic', '')
            
            if not question or not answer:
                return jsonify({'error': 'Question and answer are required'}), 400
            
            flashcard = Flashcard(
                user_id=session['user_id'],
                question=question,
                answer=answer,
                topic=topic
            )
            db.session.add(flashcard)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'flashcard': {
                    'id': flashcard.id,
                    'question': flashcard.question,
                    'answer': flashcard.answer,
                    'topic': flashcard.topic
                }
            })
        
        elif source_type == 'pdf':
            pdf_id = data.get('pdf_id')
            count = data.get('count', 10)
            
            pdf_doc = PDFDocument.query.filter_by(id=pdf_id, user_id=session['user_id']).first()
            if not pdf_doc:
                return jsonify({'error': 'PDF not found'}), 404
            
            flashcards_data = generate_flashcards_from_content(
                pdf_doc.content, 
                topic=pdf_doc.filename, 
                count=count
            )
            
        elif source_type == 'topic':
            topic = data.get('topic', '').strip()
            difficulty = data.get('difficulty', 'medium')
            count = data.get('count', 10)
            
            if not topic:
                return jsonify({'error': 'Topic is required'}), 400
            
            flashcards_data = generate_flashcards_from_content(
                "", 
                topic=topic, 
                difficulty=difficulty, 
                count=count
            )
        
        else:
            return jsonify({'error': 'Invalid source type'}), 400
        
        # Save generated flashcards
        if source_type in ['pdf', 'topic']:
            saved_flashcards = []
            for card_data in flashcards_data:
                if isinstance(card_data, dict) and 'question' in card_data and 'answer' in card_data:
                    flashcard = Flashcard(
                        user_id=session['user_id'],
                        question=card_data['question'],
                        answer=card_data['answer'],
                        topic=data.get('topic', ''),
                        difficulty=data.get('difficulty', 'medium')
                    )
                    db.session.add(flashcard)
                    saved_flashcards.append({
                        'question': flashcard.question,
                        'answer': flashcard.answer
                    })
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'flashcards': saved_flashcards,
                'count': len(saved_flashcards)
            })
    
    except Exception as e:
        app.logger.error(f"Flashcard creation error: {str(e)}")
        return jsonify({'error': 'Failed to create flashcards'}), 500

@app.route('/api/get-flashcards')
def get_flashcards():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    flashcards = Flashcard.query.filter_by(user_id=session['user_id']).order_by(Flashcard.created_at.desc()).all()
    
    return jsonify({
        'flashcards': [{
            'id': card.id,
            'question': card.question,
            'answer': card.answer,
            'topic': card.topic,
            'difficulty': card.difficulty
        } for card in flashcards]
    })

@app.route('/api/get-pdfs')
def get_pdfs():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pdfs = PDFDocument.query.filter_by(user_id=session['user_id']).order_by(PDFDocument.upload_time.desc()).all()
    
    return jsonify({
        'pdfs': [{
            'id': pdf.id,
            'filename': pdf.filename,
            'upload_time': pdf.upload_time.isoformat(),
            'content_preview': pdf.content[:200] + '...' if pdf.content else ''
        } for pdf in pdfs]
    })

@app.route('/api/delete-pdf/<int:pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pdf_doc = PDFDocument.query.filter_by(id=pdf_id, user_id=session['user_id']).first()
    if not pdf_doc:
        return jsonify({'error': 'PDF not found'}), 404
    
    try:
        # Delete file from filesystem
        if os.path.exists(pdf_doc.file_path):
            os.remove(pdf_doc.file_path)
        
        # Delete from database
        db.session.delete(pdf_doc)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'PDF deleted successfully'})
    
    except Exception as e:
        app.logger.error(f"PDF deletion error: {str(e)}")
        return jsonify({'error': 'Failed to delete PDF'}), 500

@app.route('/api/voice-to-text', methods=['POST'])
def voice_to_text():
    """Convert voice audio to text"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    try:
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            
            # Use speech recognition
            r = sr.Recognizer()
            with sr.AudioFile(temp_audio.name) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
            
            # Clean up temp file
            os.unlink(temp_audio.name)
            
            return jsonify({'text': text})
    
    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand audio'}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Speech recognition service error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Voice to text error: {str(e)}")
        return jsonify({'error': 'Failed to process audio'}), 500

@app.route('/api/text-to-voice', methods=['POST'])
def text_to_voice():
    """Convert text to voice audio"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Generate speech
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            tts.save(temp_audio.name)
            
            # Read file content
            with open(temp_audio.name, 'rb') as f:
                audio_data = f.read()
            
            # Clean up temp file
            os.unlink(temp_audio.name)
            
            return audio_data, 200, {
                'Content-Type': 'audio/mpeg',
                'Content-Disposition': 'attachment; filename=response.mp3'
            }
    
    except Exception as e:
        app.logger.error(f"Text to voice error: {str(e)}")
        return jsonify({'error': 'Failed to generate audio'}), 500

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
