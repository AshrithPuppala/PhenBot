from flask import Flask, request, jsonify, render_template_string
import os
import sys
import subprocess
import importlib

app = Flask(__name__)

# Debug info
print("=== DEPLOYMENT DEBUG ===")
print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Get API key
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
print(f"API Key found: {bool(GROQ_API_KEY)}")

# Multiple attempt Groq initialization
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = "Not attempted"

def try_install_groq():
    """Try to install groq if not available"""
    try:
        print("Attempting to install groq...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "groq==0.4.1", "--quiet"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("Groq installation successful")
            return True
        else:
            print(f"Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Installation error: {e}")
        return False

def initialize_groq():
    """Try multiple methods to get Groq working"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    if not GROQ_API_KEY:
        GROQ_ERROR = "No API key found"
        return
    
    # Method 1: Direct import
    try:
        print("Method 1: Direct import...")
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
        print("✅ Method 1 successful")
        return
    except ImportError as e:
        print(f"Method 1 failed - Import error: {e}")
        # Try installing
        if try_install_groq():
            try:
                importlib.invalidate_caches()
                from groq import Groq
                groq_client = Groq(api_key=GROQ_API_KEY)
                GROQ_AVAILABLE = True
                print("✅ Post-install import successful")
                return
            except Exception as e2:
                print(f"Post-install failed: {e2}")
        
    except Exception as e:
        print(f"Method 1 failed - Other error: {e}")
    
    # Method 2: Try different versions
    for version in ["0.4.1", "0.5.0", "0.8.0"]:
        try:
            print(f"Method 2: Trying groq=={version}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", f"groq=={version}", "--quiet", "--force-reinstall"
            ], check=True, timeout=60)
            
            importlib.invalidate_caches()
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY)
            GROQ_AVAILABLE = True
            print(f"✅ Method 2 successful with version {version}")
            return
            
        except Exception as e:
            print(f"Method 2 failed for version {version}: {e}")
            continue
    
    GROQ_ERROR = "All initialization methods failed"

# Initialize Groq
initialize_groq()

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
  .info { background: #d1ecf1; color: #0c5460; border: 2px solid #bee5eb; }
  
  .debug {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    max-height: 200px;
    overflow-y: auto;
  }
  
  #messages { 
    height: 350px; 
    overflow-y: auto; 
    border: 1px solid #e1e5e9; 
    padding: 20px;
    margin: 20px 0; 
    background: #f8f9fa;
    border-radius: 15px;
  }
  .message {
    margin: 12px 0;
    padding: 12px 18px;
    border-radius: 18px;
    max-width: 85%;
    word-wrap: break-word;
    line-height: 1.4;
  }
  .user-msg { 
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    margin-left: auto;
    text-align: right;
    border-bottom-right-radius: 6px;
  }
  .bot-msg { 
    background: #e9ecef;
    color: #333;
    border-bottom-left-radius: 6px;
  }
  .welcome-msg {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
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
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
  }
  #sendBtn, .btn {
    padding: 15px 25px; 
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none; 
    border-radius: 25px; 
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    margin: 5px;
    transition: all 0.3s ease;
  }
  #sendBtn:hover:not(:disabled), .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
  }
  #sendBtn:disabled { 
    background: #6c757d; 
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  .retry-section {
    text-align: center;
    margin: 20px 0;
  }
</style>
</head>
<body>
<div class="container">
  <h2>🤖 PhenBOT Study Companion</h2>
  
  <div id="app-status" class="status info">Checking AI systems...</div>
  
  <div id="debug-info" class="debug" style="display: none;"></div>
  
  <div class="retry-section">
    <button class="btn" onclick="retryConnection()">🔄 Retry Connection</button>
    <button class="btn" onclick="showDebug()">🔍 Show Debug</button>
    <button class="btn" onclick="forceReinstall()">🛠️ Force Repair</button>
  </div>
  
  <div id="messages">
    <div class="message bot-msg welcome-msg">
      Hello! I'm PhenBOT, your AI study companion. I'm checking my systems...
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
  const debugDiv = document.getElementById('debug-info');
  
  try {
    statusDiv.textContent = '🔄 Checking AI systems...';
    statusDiv.className = 'status info';
    
    const response = await fetch('/health');
    const data = await response.json();
    
    console.log('Health check:', data);
    
    debugDiv.innerHTML = `
      <strong>System Diagnostics:</strong><br>
      API Key Present: ${data.api_key_present}<br>
      Groq Available: ${data.groq_available}<br>
      Python Version: ${data.python_version}<br>
      Error: ${data.error}<br>
      Working Dir: ${data.working_dir}<br>
      Packages: ${data.installed_packages || 'Loading...'}
    `;
    
    if (data.groq_available && data.api_key_present) {
      statusDiv.textContent = '✅ All systems operational! Ready to help!';
      statusDiv.className = 'status success';
      isReady = true;
      updateSendButton();
      addMessage('bot-msg', 'Great! My AI brain is now online and ready to help with your studies!');
    } else if (!data.groq_available) {
      statusDiv.textContent = '❌ AI library not loaded - trying repair...';
      statusDiv.className = 'status error';
      // Auto-attempt repair
      setTimeout(() => forceReinstall(), 2000);
    } else if (!data.api_key_present) {
      statusDiv.textContent = '⚠️ API key missing - check Railway environment variables';
      statusDiv.className = 'status warning';
    }
  } catch (error) {
    statusDiv.textContent = '❌ Connection failed - check deployment';
    statusDiv.className = 'status error';
    console.error('Status check failed:', error);
  }
}

function addMessage(className, text) {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = `message ${className}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function updateSendButton() {
  const sendBtn = document.getElementById('sendBtn');
  const question = document.getElementById('question').value.trim();
  sendBtn.disabled = !question || !isReady;
}

async function retryConnection() {
  addMessage('bot-msg', 'Retrying connection to AI systems...');
  checkStatus();
}

function showDebug() {
  const debugDiv = document.getElementById('debug-info');
  debugDiv.style.display = debugDiv.style.display === 'none' ? 'block' : 'none';
}

async function forceReinstall() {
  addMessage('bot-msg', 'Attempting to repair AI systems... This may take a moment.');
  try {
    const response = await fetch('/repair', { method: 'POST' });
    const data = await response.json();
    addMessage('bot-msg', data.message || 'Repair attempted');
    setTimeout(() => checkStatus(), 3000);
  } catch (error) {
    addMessage('bot-msg', 'Repair failed: ' + error.message);
  }
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
  
  addMessage('user-msg', question);
  questionInput.value = '';
  updateSendButton();
  
  const thinkingMsg = addMessage('bot-msg', '🤔 Thinking...');
  
  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: question})
    });
    
    const data = await response.json();
    
    // Remove thinking message
    thinkingMsg.remove();
    
    addMessage('bot-msg', data.answer || data.error || 'Sorry, no response generated.');
    
  } catch (error) {
    thinkingMsg.remove();
    addMessage('bot-msg', `Error: ${error.message}`);
  }
  
  document.getElementById('question').focus();
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
    # Get installed packages
    try:
        import pkg_resources
        packages = [f"{pkg.project_name}=={pkg.version}" for pkg in pkg_resources.working_set]
        groq_packages = [p for p in packages if 'groq' in p.lower()]
    except:
        groq_packages = ["Unable to check packages"]
    
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(GROQ_API_KEY),
        'error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'working_dir': os.getcwd(),
        'installed_packages': groq_packages
    })

@app.route('/repair', methods=['POST'])
def repair():
    """Try to repair the Groq installation"""
    try:
        global groq_client, GROQ_AVAILABLE, GROQ_ERROR
        
        # Force reinstall
        print("Starting repair process...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "groq==0.4.1", "--force-reinstall", "--no-cache-dir"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            return jsonify({'message': f'Repair failed: {result.stderr}'})
        
        # Try to re-import
        import importlib
        if 'groq' in sys.modules:
            importlib.reload(sys.modules['groq'])
        
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
        GROQ_ERROR = None
        
        return jsonify({'message': 'Repair successful! AI systems restored.'})
        
    except Exception as e:
        return jsonify({'message': f'Repair failed: {str(e)}'})

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'AI system offline: {GROQ_ERROR}'}), 500
        
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please ask a question'}), 400

        response = groq_client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": "You are PhenBOT, a helpful academic study companion. Provide clear, educational answers."
            }, {
                "role": "user", 
                "content": question
            }],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500
        )
        
        return jsonify({'answer': response.choices[0].message.content})
        
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting PhenBOT on port {port}")
    print(f"🔑 Groq Status: {GROQ_AVAILABLE}")
    if GROQ_ERROR:
        print(f"❌ Error: {GROQ_ERROR}")
    app.run(host='0.0.0.0', port=port, debug=False)
