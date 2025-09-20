# app.py -- Fixed version with proper HTML template
from flask import Flask, request, jsonify, render_template_string
import os
import sys
import threading

app = Flask(__name__)

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None
_init_lock = threading.Lock()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'/>
    <meta name='viewport' content='width=device-width,initial-scale=1'/>
    <title>PhenBOT Study Companion</title>
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --accent-color: #4facfe;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--primary-gradient);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 20px;
        }
        
        #main { 
            max-width: 800px;
            background: var(--card-bg);
            margin: 0 auto;
            padding: 32px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo {
            background: var(--secondary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .tagline {
            color: var(--text-secondary);
            font-size: 18px;
        }
        
        #messages { 
            height: 400px;
            overflow-y: auto;
            border: 2px solid var(--border-color);
            padding: 20px;
            background: #f8f9fa;
            margin-bottom: 20px;
            border-radius: 16px;
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 16px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-msg { 
            background: var(--accent-color);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .bot-msg { 
            background: #e3f2fd;
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
            border-left: 4px solid var(--accent-color);
        }
        
        .input-container {
            display: flex;
            gap: 12px;
            align-items: stretch;
        }
        
        #question { 
            flex: 1;
            padding: 16px 20px;
            border: 2px solid var(--border-color);
            border-radius: 25px;
            outline: none;
            font-size: 16px;
            font-family: inherit;
            transition: border-color 0.3s ease;
        }
        
        #question:focus {
            border-color: var(--accent-color);
        }
        
        #sendBtn { 
            background: var(--secondary-gradient);
            color: white;
            border: none;
            padding: 16px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.3s ease;
            min-width: 100px;
        }
        
        #sendBtn:hover:not(:disabled) {
            transform: translateY(-2px);
        }
        
        #sendBtn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            text-align: center;
            margin-top: 20px;
            padding: 16px;
            border-radius: 12px;
            font-weight: 500;
        }
        
        .status.error {
            background: #fee2e2;
            color: var(--error-color);
            border: 1px solid #fca5a5;
        }
        
        .status.success {
            background: #ecfdf5;
            color: var(--success-color);
            border: 1px solid #86efac;
        }
        
        .typing-indicator {
            display: none;
            background: #e3f2fd;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 16px;
            max-width: 80%;
            border-left: 4px solid var(--accent-color);
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-color);
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
    </style>
</head>
<body>
    <div id='main'>
        <div class="header">
            <div class="logo">🤖 PhenBOT</div>
            <div class="tagline">Advanced Study Companion</div>
        </div>
        
        <div id='messages'>
            <div class="bot-msg">
                Welcome to PhenBOT! I'm your AI study companion, ready to help you learn through personalized explanations, analogies, and interactive learning. Ask me anything about your studies!
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span style="margin-left: 12px;">PhenBOT is thinking...</span>
        </div>
        
        <div class="input-container">
            <input id='question' placeholder='Ask me a study question...' autocomplete='off'/>
            <button id='sendBtn' disabled>Send</button>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>
    
    <script>
        const questionInput = document.getElementById('question');
        const sendBtn = document.getElementById('sendBtn');
        const messagesDiv = document.getElementById('messages');
        const typingIndicator = document.getElementById('typingIndicator');
        const statusDiv = document.getElementById('status');
        
        questionInput.oninput = () => {
            sendBtn.disabled = !questionInput.value.trim();
        };
        
        sendBtn.onclick = sendMessage;
        questionInput.onkeypress = e => {
            if (e.key === 'Enter' && !sendBtn.disabled) {
                sendMessage();
            }
        };
        
        function appendMessage(type, text) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.innerText = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function showTyping() {
            typingIndicator.style.display = 'block';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function hideTyping() {
            typingIndicator.style.display = 'none';
        }
        
        function showStatus(message, type = 'error') {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
        
        async function sendMessage() {
            const text = questionInput.value.trim();
            if (!text) return;
            
            appendMessage('user-msg', text);
            questionInput.value = '';
            sendBtn.disabled = true;
            showTyping();
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ question: text })
                });
                
                hideTyping();
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.error) {
                    appendMessage('bot-msg', `Sorry, I encountered an error: ${data.error}`);
                    showStatus(data.error, 'error');
                } else if (data.answer) {
                    appendMessage('bot-msg', data.answer);
                } else {
                    appendMessage('bot-msg', 'I received an empty response. Please try again.');
                }
                
            } catch (error) {
                hideTyping();
                console.error('Request failed:', error);
                appendMessage('bot-msg', 'Sorry, I encountered a connection error. Please check your internet connection and try again.');
                showStatus('Connection error - please try again', 'error');
            }
        }
        
        // Check system status on load
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'healthy') {
                    showStatus('PhenBOT is ready to help!', 'success');
                } else {
                    showStatus(`System status: ${data.groq_error || 'Unknown error'}`, 'error');
                }
            })
            .catch(error => {
                console.error('Health check failed:', error);
                showStatus('Unable to check system status', 'error');
            });
    </script>
</body>
</html>
"""

def httpx_is_compatible():
    """Return True if installed httpx version is compatible with Groq (<0.28)"""
    try:
        import httpx
        ver = httpx.__version__.split(".")
        major = int(ver[0]) if len(ver) > 0 else 0
        minor = int(ver[1]) if len(ver) > 1 else 0
        # httpx 0.28 and above removed proxies; we require <0.28
        if major == 0 and minor >= 28:
            return False
        return True
    except Exception:
        # httpx not installed -> incompatible for Groq usage
        return False

def initialize_groq(force=False):
    """Attempt to import and initialize the Groq client once (thread-safe)."""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    with _init_lock:
        if GROQ_AVAILABLE and not force:
            return
        GROQ_ERROR = None

        # First check httpx compatibility
        if not httpx_is_compatible():
            GROQ_ERROR = (
                "Incompatible httpx version detected. "
                "Groq requires httpx < 0.28 (e.g. httpx==0.27.2). "
                "Please pin httpx in requirements.txt and redeploy."
            )
            print("GROQ ERROR:", GROQ_ERROR, file=sys.stderr)
            GROQ_AVAILABLE = False
            return

        try:
            from groq import Groq
        except Exception as e:
            GROQ_ERROR = f"Groq import failed: {e}"
            print("GROQ ERROR:", GROQ_ERROR, file=sys.stderr)
            GROQ_AVAILABLE = False
            return

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            GROQ_ERROR = "GROQ_API_KEY env var missing"
            print("GROQ ERROR:", GROQ_ERROR, file=sys.stderr)
            GROQ_AVAILABLE = False
            return

        try:
            # instantiate Groq (wrapped in try to catch TypeError about proxies)
            groq_client = Groq(api_key=api_key)
            GROQ_AVAILABLE = True
            GROQ_ERROR = None
            print("Groq client initialized successfully")
        except TypeError as e:
            # Common case: httpx removed proxies argument -> return actionable message
            if "proxies" in str(e):
                GROQ_ERROR = (
                    "Groq initialization failed due to incompatible httpx version "
                    "(proxies argument missing). Pin httpx<0.28 (e.g. httpx==0.27.2)."
                )
            else:
                GROQ_ERROR = f"Groq initialization failed: {e}"
            print("GROQ ERROR:", GROQ_ERROR, file=sys.stderr)
            GROQ_AVAILABLE = False
        except Exception as e:
            GROQ_ERROR = f"Groq initialization failed: {e}"
            print("GROQ ERROR:", GROQ_ERROR, file=sys.stderr)
            GROQ_AVAILABLE = False

# Initialize Groq on startup
initialize_groq()

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    # Try to initialize if not available (helps in ephemeral environments)
    if not GROQ_AVAILABLE:
        initialize_groq()
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'groq_error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'status': 'healthy' if GROQ_AVAILABLE else 'error',
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    # Ensure Groq available (try to initialize once more)
    if not GROQ_AVAILABLE:
        initialize_groq()
    if not GROQ_AVAILABLE:
        return jsonify({'error': f'Groq not available: {GROQ_ERROR}'}), 500

    data = request.get_json() or {}
    question = data.get('question','').strip()
    if not question:
        return jsonify({'error': 'Please enter a question.'}), 400

    try:
        # Enhanced system prompt for PhenBOT
        system_prompt = """You are PhenBOT, an advanced AI study companion with these capabilities:

1. **Personalized Learning**: Provide concise, curriculum-focused answers
2. **Analogy-Based Learning**: Use relatable analogies to explain complex concepts
3. **Active Learning**: After explaining, ask students to explain back in their own words
4. **Accuracy**: Provide reliable, well-researched information
5. **Student-Friendly**: Use clear, engaging language appropriate for the learning level

Always:
- Give accurate, helpful answers
- Use analogies when explaining difficult concepts
- Encourage active learning by asking follow-up questions
- Be encouraging and supportive
- Keep responses concise but comprehensive
"""

        response = groq_client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': question}
            ],
            model='llama-3.1-8b-instant',
            temperature=0.7,
            max_tokens=500
        )
        return jsonify({'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f'Groq API error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting local dev server on :{port} (GROQ_AVAILABLE={GROQ_AVAILABLE})")
    app.run(host='0.0.0.0', port=port, debug=False)
