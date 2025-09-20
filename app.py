from flask import Flask, request, jsonify, render_template_string
import os
import sys

app = Flask(__name__)

# Get API key
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
print(f"API Key present: {bool(GROQ_API_KEY)}")

# Try to import and initialize Groq with proper error handling
GROQ_AVAILABLE = False
GROQ_ERROR = None
groq_client = None

try:
    print("Attempting to import groq...")
    from groq import Groq
    print("✅ Groq imported successfully")
    
    if GROQ_API_KEY:
        print("Creating Groq client...")
        # Use minimal parameters to avoid compatibility issues
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client created successfully")
        GROQ_AVAILABLE = True
    else:
        GROQ_ERROR = "API key not found"
        
except Exception as e:
    print(f"❌ Groq error: {str(e)}")
    GROQ_ERROR = str(e)

# HTML template for the working app
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PhenBOT Study Companion</title>
<style>
  body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
    margin: 0; 
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
  }
  .container { 
    max-width: 700px; 
    margin: 0 auto; 
    padding: 25px; 
    background: white; 
    border-radius: 20px; 
    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
  }
  h2 {
    text-align: center;
    color: #333;
    margin-bottom: 20px;
    font-size: 28px;
  }
  .status {
    padding: 15px;
    margin: 15px 0;
    border-radius: 10px;
    text-align: center;
    font-weight: 600;
  }
  .success { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
  .error { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
  .warning { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
  
  #messages { 
    height: 400px; 
    overflow-y: auto; 
    border: 1px solid #e1e5e9; 
    padding: 20px;
    margin: 20px 0; 
    background: #f8f9fa;
    border-radius: 15px;
  }
  .message {
    margin: 15px 0;
    padding: 12px 18px;
    border-radius: 20px;
    max-width: 85%;
    word-wrap: break-word;
    animation: slideIn 0.3s ease-out;
    line-height: 1.4;
  }
  .user-msg { 
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    margin-left: auto;
    text-align: right;
    border-bottom-right-radius: 8px;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  }
  .bot-msg { 
    background: #e9ecef;
    color: #333;
    border-bottom-left-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  .welcome-msg {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
  }
  .input-group {
    display: flex;
    gap: 15px;
    align-items: stretch;
  }
  #question { 
    flex: 1;
    padding: 18px 25px; 
    border: 2px solid #e1e5e9;
    border-radius: 30px;
    font-size: 16px;
    outline: none;
    transition: all 0.3s ease;
  }
  #question:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
  }
  #sendBtn {
    padding: 18px 30px; 
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none; 
    border-radius: 30px; 
    cursor: pointer;
    font-size: 16px;
    font-weight: 700;
    transition: all 0.3s ease;
    min-width: 100px;
  }
  #sendBtn:hover:not(:disabled) {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  }
  #sendBtn:disabled { 
    background: #6c757d; 
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
  }
  .loading {
    opacity: 0.8;
    font-style: italic;
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 0.5; }
  }
  .typing {
    display: inline-block;
  }
  .typing::after {
    content: '';
    animation: typing 1.5s infinite;
  }
  @keyframes typing {
    0%, 33% { content: '.'; }
    34%, 66% { content: '..'; }
    67%, 100% { content: '...'; }
  }
</style>
</head>
<body>
<div class="container">
  <h2>🤖 PhenBOT Study Companion</h2>
  
  <div id="app-status" class="status">Checking systems...</div>
  
  <div id="messages">
    <div class="message bot-msg welcome-msg">
      Hello! I'm PhenBOT, your AI study companion. I'm here to help you with any academic questions you have!
    </div>
  </div>
  
  <div class="input-group">
    <input type="text" id="question" placeholder="Ask me anything about your studies..." />
    <button id="sendBtn" disabled>Send</button>
  </div>
</div>

<script>
let isReady = false;

async function checkStatus() {
  const statusDiv = document.getElementById('app-status');
  
  try {
    const response = await fetch('/health');
    const data = await response.json();
    
    console.log('Health check:', data);
    
    if (data.groq_available && data.api_key_present) {
      statusDiv.textContent = '✅ All systems ready! Ask me anything!';
      statusDiv.className = 'status success';
      isReady = true;
      updateSendButton();
      
      // Add a ready message
      setTimeout(() => {
        const messages = document.getElementById('messages');
        const readyMsg = document.createElement('div');
        readyMsg.className = 'message bot-msg';
        readyMsg.textContent = 'My AI brain is now online and ready to help with your studies! What would you like to learn about?';
        messages.appendChild(readyMsg);
        messages.scrollTop = messages.scrollHeight;
      }, 1000);
      
    } else if (!data.groq_available) {
      statusDiv.textContent = '❌ AI system unavailable - check deployment';
      statusDiv.className = 'status error';
    } else if (!data.api_key_present) {
      statusDiv.textContent = '⚠️ API configuration issue';
      statusDiv.className = 'status warning';
    }
  } catch (error) {
    statusDiv.textContent = '❌ Connection failed';
    statusDiv.className = 'status error';
  }
}

function updateSendButton() {
  const sendBtn = document.getElementById('sendBtn');
  const question = document.getElementById('question').value.trim();
  sendBtn.disabled = !question || !isReady;
}

document.getElementById('question').addEventListener('input', updateSendButton);
document.getElementById('question').addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !document.getElementById('sendBtn').disabled) {
    sendQuestion();
  }
});

async function sendQuestion() {
  const questionInput = document.getElementById('question');
  const question = questionInput.value.trim();
  if (!question || !isReady) return;
  
  const messages = document.getElementById('messages');
  
  // Add user message
  const userDiv = document.createElement('div');
  userDiv.className = 'message user-msg';
  userDiv.textContent = question;
  messages.appendChild(userDiv);
  
  questionInput.value = '';
  updateSendButton();
  
  // Add typing indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message bot-msg loading';
  typingDiv.innerHTML = '🤔 <span class="typing">Thinking</span>';
  messages.appendChild(typingDiv);
  messages.scrollTop = messages.scrollHeight;
  
  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: question})
    });
    
    const data = await response.json();
    
    // Remove typing indicator
    if (typingDiv.parentNode) {
      typingDiv.parentNode.removeChild(typingDiv);
    }
    
    // Add bot response
    const botDiv = document.createElement('div');
    botDiv.className = 'message bot-msg';
    botDiv.textContent = data.answer || data.error || 'Sorry, I could not generate a response.';
    messages.appendChild(botDiv);
    
  } catch (error) {
    // Remove typing indicator
    if (typingDiv.parentNode) {
      typingDiv.parentNode.removeChild(typingDiv);
    }
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message bot-msg';
    errorDiv.style.background = '#f8d7da';
    errorDiv.style.color = '#721c24';
    errorDiv.textContent = `I encountered an error: ${error.message}`;
    messages.appendChild(errorDiv);
  }
  
  messages.scrollTop = messages.scrollHeight;
  questionInput.focus();
}

document.getElementById('sendBtn').addEventListener('click', sendQuestion);

// Initialize
window.addEventListener('load', () => {
  checkStatus();
  document.getElementById('question').focus();
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(GROQ_API_KEY),
        'error': GROQ_ERROR
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'AI system not available: {GROQ_ERROR}'}), 500
        
        if not groq_client:
            return jsonify({'error': 'AI client not initialized'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No question received'}), 400
            
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please ask a question'}), 400

        print(f"Processing question: {question}")

        # Make API call to Groq
        response = groq_client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": "You are PhenBOT, a helpful and knowledgeable academic study companion. Provide clear, accurate, and educational answers to help students learn. Keep responses concise but informative."
            }, {
                "role": "user", 
                "content": question
            }],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        print(f"Generated response: {answer[:100]}...")
        
        return jsonify({'answer': answer})
        
    except Exception as e:
        error_msg = f'Error processing your question: {str(e)}'
        print(f"API error: {error_msg}")
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting PhenBOT on port {port}")
    print(f"🔑 API configured: {GROQ_AVAILABLE}")
    app.run(host='0.0.0.0', port=port, debug=False)
