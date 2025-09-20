from flask import Flask, request, jsonify, render_template_string
import os
import sys

app = Flask(__name__)

# Initialize Groq client
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initialize Groq client with proper error handling"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    try:
        from groq import Groq
        
        # Get API key from environment variable (Railway)
        GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
        
        if not GROQ_API_KEY:
            GROQ_ERROR = "GROQ_API_KEY environment variable not found"
            print("Error: GROQ_API_KEY not found in environment variables", file=sys.stderr)
            return False
        
        # Initialize Groq client
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
        return True
        
    except ImportError:
        GROQ_ERROR = "Groq library not installed"
        print("Error: Groq library not available", file=sys.stderr)
        return False
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {str(e)}"
        print(f"Error initializing Groq client: {e}", file=sys.stderr)
        return False

def ask_study_bot(question):
    """
    Sends an academic question to the Groq API and returns the answer.
    """
    if not groq_client:
        return "Study bot is not available. Please check the API key configuration."

    prompt = f"As PhenBOT, a knowledgeable academic assistant, answer the following question clearly and helpfully: {question}"

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are PhenBOT, a helpful academic study companion. Provide clear, accurate, and educational answers to help students learn. Keep responses informative but concise."
                },
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"I encountered an error while processing your question: {str(e)}"

# Initialize Groq on startup
initialize_groq()

# HTML Frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT Study Companion</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .status-bar {
            padding: 15px 30px;
            border-bottom: 1px solid #eee;
        }
        
        .status {
            padding: 10px 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .chat-container {
            height: 500px;
            padding: 30px;
        }
        
        .messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e1e5e9;
            border-radius: 15px;
            padding: 20px;
            background: #f8f9fa;
            margin-bottom: 20px;
        }
        
        .message {
            margin: 15px 0;
            padding: 12px 18px;
            border-radius: 18px;
            max-width: 80%;
            line-height: 1.5;
            animation: fadeIn 0.3s ease-in;
        }
        
        .message.user {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 6px;
        }
        
        .message.bot {
            background: #e9ecef;
            color: #333;
            border-bottom-left-radius: 6px;
        }
        
        .message.welcome {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            max-width: 100%;
            text-align: center;
        }
        
        .message.loading {
            background: #e9ecef;
            color: #666;
            font-style: italic;
            opacity: 0.8;
        }
        
        .input-container {
            display: flex;
            gap: 15px;
            align-items: stretch;
        }
        
        #questionInput {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        #questionInput:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
        }
        
        #sendButton {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 100px;
        }
        
        #sendButton:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        #sendButton:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .typing-animation::after {
            content: '';
            animation: dots 1.5s infinite;
        }
        
        @keyframes dots {
            0%, 33% { content: '.'; }
            34%, 66% { content: '..'; }
            67%, 100% { content: '...'; }
        }
        
        @media (max-width: 600px) {
            body { padding: 10px; }
            .header { padding: 20px; }
            .header h1 { font-size: 2em; }
            .chat-container { padding: 20px; }
            .input-container { flex-direction: column; }
            #questionInput { margin-bottom: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 PhenBOT</h1>
            <p>Your AI Study Companion</p>
        </div>
        
        <div class="status-bar">
            <div id="status" class="status">Checking system status...</div>
        </div>
        
        <div class="chat-container">
            <div id="messages" class="messages">
                <div class="message welcome">
                    Welcome to PhenBOT! I'm your AI study companion, ready to help you with any academic questions.
                </div>
            </div>
            
            <div class="input-container">
                <input 
                    type="text" 
                    id="questionInput" 
                    placeholder="Ask me any study question..."
                    autocomplete="off"
                />
                <button id="sendButton" disabled>Send</button>
            </div>
        </div>
    </div>

    <script>
        let isSystemReady = false;
        
        // DOM elements
        const statusDiv = document.getElementById('status');
        const messagesDiv = document.getElementById('messages');
        const questionInput = document.getElementById('questionInput');
        const sendButton = document.getElementById('sendButton');
        
        // Check system status
        async function checkSystemStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                if (data.groq_available && data.api_key_present) {
                    statusDiv.textContent = '✅ System Ready - AI Online';
                    statusDiv.className = 'status success';
                    isSystemReady = true;
                    
                    // Add ready message
                    setTimeout(() => {
                        addMessage('bot', "I'm now ready to help with your studies! Ask me anything about any subject.");
                    }, 1000);
                    
                } else if (!data.groq_available) {
                    statusDiv.textContent = '❌ AI System Unavailable';
                    statusDiv.className = 'status error';
                } else if (!data.api_key_present) {
                    statusDiv.textContent = '⚠️ API Key Not Configured';
                    statusDiv.className = 'status warning';
                }
                
                updateSendButton();
                
            } catch (error) {
                statusDiv.textContent = '❌ Connection Failed';
                statusDiv.className = 'status error';
                console.error('Status check failed:', error);
            }
        }
        
        // Add message to chat
        function addMessage(type, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            return messageDiv;
        }
        
        // Update send button state
        function updateSendButton() {
            const hasQuestion = questionInput.value.trim().length > 0;
            sendButton.disabled = !hasQuestion || !isSystemReady;
        }
        
        // Send question to bot
        async function sendQuestion() {
            const question = questionInput.value.trim();
            if (!question || !isSystemReady) return;
            
            // Add user message
            addMessage('user', question);
            
            // Clear input and disable button
            questionInput.value = '';
            updateSendButton();
            
            // Add loading message
            const loadingMessage = addMessage('bot loading', 'Thinking');
            loadingMessage.innerHTML = 'Thinking<span class="typing-animation"></span>';
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                // Remove loading message
                loadingMessage.remove();
                
                // Add bot response
                if (data.answer) {
                    addMessage('bot', data.answer);
                } else if (data.error) {
                    addMessage('bot', `Error: ${data.error}`);
                } else {
                    addMessage('bot', 'Sorry, I could not generate a response.');
                }
                
            } catch (error) {
                loadingMessage.remove();
                addMessage('bot', `I encountered an error: ${error.message}`);
            }
            
            // Focus back on input
            questionInput.focus();
        }
        
        // Event listeners
        questionInput.addEventListener('input', updateSendButton);
        
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !sendButton.disabled) {
                sendQuestion();
            }
        });
        
        sendButton.addEventListener('click', sendQuestion);
        
        // Initialize app
        window.addEventListener('load', () => {
            checkSystemStatus();
            questionInput.focus();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main application"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'status': 'healthy'
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """Handle study questions"""
    try:
        if not GROQ_AVAILABLE:
            return jsonify({
                'error': f'AI system not available: {GROQ_ERROR}'
            }), 500
        
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Get answer from study bot
        answer = ask_study_bot(question)
        
        return jsonify({'answer': answer})
        
    except Exception as e:
        print(f"Error in api_ask: {str(e)}", file=sys.stderr)
        return jsonify({
            'error': f'Failed to process question: {str(e)}'
        }), 500

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'PhenBOT is running!',
        'groq_status': GROQ_AVAILABLE,
        'environment': 'Railway'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting PhenBOT on port {port}")
    print(f"Groq available: {GROQ_AVAILABLE}")
    if GROQ_ERROR:
        print(f"Groq error: {GROQ_ERROR}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
