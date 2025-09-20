from flask import Flask, request, jsonify, render_template_string
import os
import sys

app = Flask(__name__)

# Enhanced debug logging
print("=== DETAILED DEBUG INFO ===")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment variables count: {len(os.environ)}")

# Get API key
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
print(f"API Key present: {bool(GROQ_API_KEY)}")
if GROQ_API_KEY:
    print(f"API Key starts with: {GROQ_API_KEY[:10]}...")

# Try to import groq with detailed error handling
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

try:
    print("Attempting to import groq...")
    import groq
    print(f"✅ Groq module imported successfully. Version: {getattr(groq, '__version__', 'unknown')}")
    
    from groq import Groq
    print("✅ Groq class imported successfully")
    
    if GROQ_API_KEY:
        print("Attempting to create Groq client...")
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client created successfully")
        GROQ_AVAILABLE = True
    else:
        print("❌ No API key provided")
        GROQ_ERROR = "API key not provided"
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    GROQ_ERROR = f"Import error: {e}"
    # Try to install groq on the fly (sometimes works in Railway)
    try:
        print("Attempting to install groq package...")
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "groq==0.4.1"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Groq installed successfully")
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
            GROQ_AVAILABLE = True
            GROQ_ERROR = None
        else:
            print(f"❌ Installation failed: {result.stderr}")
            GROQ_ERROR = f"Installation failed: {result.stderr}"
    except Exception as install_error:
        print(f"❌ Installation attempt failed: {install_error}")
        GROQ_ERROR = f"Installation attempt failed: {install_error}"
        
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    GROQ_ERROR = f"Unexpected error: {e}"

print(f"Final status - Groq available: {GROQ_AVAILABLE}")

# HTML template
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
    max-height: 200px;
    overflow-y: auto;
  }
  .instructions {
    background: #e3f2fd;
    border: 1px solid #2196f3;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
    color: #1565c0;
  }
</style>
</head>
<body>
<div class="container">
  <h2>🤖 PhenBOT Study Companion</h2>
  
  <div id="app-status" class="status warning">Checking status...</div>
  
  <div id="debug-info" class="debug-info" style="display: none;"></div>
  
  <div id="instructions" class="instructions" style="display: none;"></div>
  
  <div id="messages">
    <div class="message bot-msg">Hello! I'm PhenBOT. Let me check my systems and dependencies...</div>
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
  const instructionsDiv = document.getElementById('instructions');
  
  try {
    console.log('Checking app status...');
    const response = await fetch('/health');
    const data = await response.json();
    
    console.log('Health check response:', data);
    
    // Show debug info
    debugDiv.innerHTML = `
      <strong>System Status:</strong><br>
      Groq Available: ${data.groq_available}<br>
      API Key Present: ${data.api_key_present}<br>
      Port: ${data.port}<br>
      Python Version: ${data.python_version || 'Unknown'}<br>
      Error: ${data.groq_error || 'None'}<br>
      Working Directory: ${data.working_dir || 'Unknown'}
    `;
    debugDiv.style.display = 'block';
    
    if (data.groq_available && data.api_key_present) {
      statusDiv.textContent = '✅ All systems operational! Ready to help with your studies.';
      statusDiv.className = 'status success';
      isReady = true;
      updateSendButton();
    } else if (!data.groq_available) {
      statusDiv.textContent = '❌ Groq library not available - check deployment';
      statusDiv.className = 'status error';
      
      instructionsDiv.innerHTML = `
        <strong>🔧 Deployment Issue Detected</strong><br><br>
        The Groq library couldn't be loaded. Try these steps:<br>
        1. Check that your <code>requirements.txt</code> has: <code>groq==0.4.1</code><br>
        2. Redeploy your app in Railway<br>
        3. Check Railway deployment logs for errors<br>
        4. Try updating the Groq version to <code>groq==0.5.0</code>
      `;
      instructionsDiv.style.display = 'block';
    } else if (!data.api_key_present) {
      statusDiv.textContent = '⚠️ API key not configured';
      statusDiv.className = 'status warning';
    }
  } catch (error) {
    console.error('Status check failed:', error);
    statusDiv.textContent = '❌ Cannot connect to server';
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
    
    const data = await response.json();
    
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
        'status': 'healthy',
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(GROQ_API_KEY),
        'groq_error': GROQ_ERROR,
        'port': os.environ.get('PORT', 'not set'),
        'python_version': sys.version,
        'working_dir': os.getcwd()
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'Groq library not available. Error: {GROQ_ERROR}'}), 500
        
        if not groq_client:
            return jsonify({'error': 'Groq client not initialized'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please provide a question.'}), 400

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
        return jsonify({'answer': answer})
        
    except Exception as e:
        error_msg = f'Server error: {str(e)}'
        print(f"Error in api_ask: {error_msg}")
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
