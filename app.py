from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

# Debug environment variables
print("=== ENVIRONMENT DEBUG ===")
print(f"All environment variables: {list(os.environ.keys())}")
print(f"PORT: {os.environ.get('PORT', 'NOT SET')}")
print(f"GROQ_API_KEY present: {bool(os.environ.get('GROQ_API_KEY'))}")
if os.environ.get('GROQ_API_KEY'):
    print(f"GROQ_API_KEY length: {len(os.environ.get('GROQ_API_KEY'))}")

# Try multiple possible environment variable names
GROQ_API_KEY = (
    os.environ.get('GROQ_API_KEY') or 
    os.environ.get('GROQ_API_KEY_PRODUCTION') or
    os.environ.get('API_KEY') or
    os.environ.get('OPENAI_API_KEY')  # Just in case
)

print(f"Final API key found: {bool(GROQ_API_KEY)}")

# Test if we can import groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    if groq_client:
        print("✅ Groq client initialized successfully")
    else:
        print("❌ Groq client not initialized - missing API key")
except Exception as e:
    GROQ_AVAILABLE = False
    groq_client = None
    print(f"❌ Groq import failed: {e}")

# HTML template with fixed JavaScript
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
    padding: 20px; 
    background: white; 
    border-radius: 15px; 
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  }
  .status {
    padding: 12px;
    margin: 15px 0;
    border-radius: 8px;
    text-align: center;
    font-weight: 500;
  }
  .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
  .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
  .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
  
  #messages { 
    height: 350px; 
    overflow-y: auto; 
    border: 1px solid #e1e5e9; 
    padding: 15px;
    margin: 15px 0; 
    background: #f8f9fa;
    border-radius: 10px;
  }
  .message {
    margin: 10px 0;
    padding: 10px 15px;
    border-radius: 18px;
    max-width: 80%;
    word-wrap: break-word;
    animation: fadeIn 0.3s ease-in;
  }
  .user-msg { 
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    margin-left: auto;
    text-align: right;
    border-bottom-right-radius: 5px;
  }
  .bot-msg { 
    background: #e9ecef;
    color: #333;
    border-bottom-left-radius: 5px;
  }
  .input-group {
    display: flex;
    gap: 12px;
    align-items: stretch;
  }
  #question { 
    flex: 1;
    padding: 15px 20px; 
    border: 2px solid #e1e5e9;
    border-radius: 25px;
    font-size: 16px;
    outline: none;
    transition: all 0.3s ease;
  }
  #question:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  #sendBtn {
    padding: 15px 25px; 
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none; 
    border-radius: 25px; 
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all 0.3s ease;
    min-width: 80px;
  }
  #sendBtn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
  }
  #sendBtn:disabled { 
    background: #6c757d; 
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .loading {
    opacity: 0.7;
    font-style: italic;
  }
  .debug-info {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
    font-family: monospace;
    font-size: 12px;
    color: #6c757d;
  }
</style>
</head>
<body>
<div class="container">
  <h2>🤖 PhenBOT Study Companion</h2>
  
  <div id="app-status" class="status warning">Checking status...</div>
  
  <div id="debug-info" class="debug-info" style="display: none;"></div>
  
  <div id="messages">
    <div class="message bot-msg">Hello! I'm PhenBOT. Let me check my systems and API configuration...</div>
  </div>
  
  <div class="input-group">
    <input type="text" id="question" placeholder="Ask a study question..." />
    <button id="sendBtn" disabled>Send</button>
  </div>
</div>

<script>
let isReady = false;

async function checkStatus() {
  const statusDiv = document.getElementById('app-status');
  const debugDiv = document.getElementById('debug-info');
  
  try {
    console.log('Checking app status...');
    const response = await fetch('/health');
    const data = await response.json();
    
    console.log('Health check response:', data);
    
    // Show debug info
    debugDiv.innerHTML = `
      <strong>Debug Info:</strong><br>
      Groq Available: ${data.groq_available}<br>
      API Key Present: ${data.api_key_present}<br>
      Port: ${data.port}<br>
      Environment Keys: ${data.env_keys || 'Not available'}
    `;
    debugDiv.style.display = 'block';
    
    if (data.groq_available && data.api_key_present) {
      statusDiv.textContent = '✅ All systems operational! Ready to help with your studies.';
      statusDiv.className = 'status success';
      isReady = true;
      updateSendButton();
    } else if (!data.groq_available) {
      statusDiv.textContent = '❌ Groq library not available - check deployment logs';
      statusDiv.className = 'status error';
    } else if (!data.api_key_present) {
      statusDiv.textContent = '⚠️ API key not configured - check Railway environment variables';
      statusDiv.className = 'status warning';
    }
  } catch (error) {
    console.error('Status check failed:', error);
    statusDiv.textContent = '❌ Cannot connect to server - check deployment';
    statusDiv.className = 'status error';
    debugDiv.innerHTML = `<strong>Connection Error:</strong> ${error.message}`;
    debugDiv.style.display = 'block';
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
  
  console.log('Sending question:', question);
  
  const messages = document.getElementById('messages');
  
  // Add user message
  const userDiv = document.createElement('div');
  userDiv.className = 'message user-msg';
  userDiv.textContent = question;
  messages.appendChild(userDiv);
  
  questionInput.value = '';
  updateSendButton();
  
  // Add thinking message
  const thinkingDiv = document.createElement('div');
  thinkingDiv.className = 'message bot-msg loading';
  thinkingDiv.textContent = '🤔 Thinking...';
  messages.appendChild(thinkingDiv);
  messages.scrollTop = messages.scrollHeight;
  
  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: question})
    });
    
    console.log('API response status:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('API response data:', data);
    
    // Remove thinking message
    if (thinkingDiv.parentNode) {
      thinkingDiv.parentNode.removeChild(thinkingDiv);
    }
    
    // Add bot response
    const botDiv = document.createElement('div');
    botDiv.className = 'message bot-msg';
    botDiv.textContent = data.answer || data.error || 'No response received';
    messages.appendChild(botDiv);
    
  } catch (error) {
    console.error('Error sending question:', error);
    
    // Remove thinking message
    if (thinkingDiv.parentNode) {
      thinkingDiv.parentNode.removeChild(thinkingDiv);
    }
    
    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message bot-msg';
    errorDiv.style.background = '#f8d7da';
    errorDiv.style.color = '#721c24';
    errorDiv.textContent = `Error: ${error.message}`;
    messages.appendChild(errorDiv);
  }
  
  messages.scrollTop = messages.scrollHeight;
  questionInput.focus();
}

document.getElementById('sendBtn').addEventListener('click', sendQuestion);

// Initialize when page loads
window.addEventListener('load', () => {
  console.log('Page loaded, checking status...');
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
        'status': 'healthy',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(GROQ_API_KEY),
        'port': os.environ.get('PORT', 'not set'),
        'env_keys': list(os.environ.keys())[:10]  # Show first 10 env vars for debugging
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        print(f"API ask called. Groq available: {GROQ_AVAILABLE}, Client: {bool(groq_client)}")
        
        if not GROQ_AVAILABLE:
            return jsonify({'error': 'Groq library not available. Check requirements.txt and deployment logs.'}), 500
        
        if not groq_client:
            return jsonify({'error': 'Groq API key not configured. Please set GROQ_API_KEY environment variable in Railway.'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        question = data.get('question', '').strip()
        print(f"Question received: {question}")
        
        if not question:
            return jsonify({'error': 'Please provide a question.'}), 400

        # Make API call
        print("Making Groq API call...")
        response = groq_client.chat.completions.create(
            messages=[{
                "role": "user", 
                "content": f"You are PhenBOT, a helpful academic study companion. Please provide a clear, educational answer to this question: {question}"
            }],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=400
        )
        
        answer = response.choices[0].message.content
        print(f"Got response: {answer[:100]}...")
        
        return jsonify({'answer': answer})
        
    except Exception as e:
        error_msg = f'Server error: {str(e)}'
        print(f"Error in api_ask: {error_msg}")
        return jsonify({'error': error_msg}), 500

@app.route('/test')
def test():
    return jsonify({
        'message': 'Flask app is running!',
        'port': os.environ.get('PORT', 'default'),
        'groq_available': GROQ_AVAILABLE,
        'api_key_configured': bool(GROQ_API_KEY)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    print(f"🔑 API key configured: {bool(GROQ_API_KEY)}")
    app.run(host='0.0.0.0', port=port, debug=False)
