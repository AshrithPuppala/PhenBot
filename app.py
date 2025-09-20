from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

# Test if we can import groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    print(f"Groq import successful. API key present: {bool(GROQ_API_KEY)}")
except Exception as e:
    GROQ_AVAILABLE = False
    groq_client = None
    print(f"Groq import failed: {e}")

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PhenBOT Study Companion</title>
<style>
  body { 
    font-family: Arial, sans-serif; 
    margin: 20px; 
    background: #f0f2f5;
    line-height: 1.6;
  }
  .container { 
    max-width: 700px; 
    margin: 0 auto; 
    padding: 20px; 
    background: white; 
    border-radius: 10px; 
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }
  .status {
    padding: 10px;
    margin: 10px 0;
    border-radius: 5px;
    text-align: center;
  }
  .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
  .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
  .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
  
  #messages { 
    height: 300px; 
    overflow-y: auto; 
    border: 1px solid #ddd; 
    padding: 10px;
    margin: 10px 0; 
    background: #fafafa;
    border-radius: 5px;
  }
  .user-msg { 
    text-align: right; 
    background: #007bff;
    color: white;
    padding: 8px 12px; 
    margin: 5px 0; 
    border-radius: 15px 15px 5px 15px;
    max-width: 80%;
    margin-left: auto;
  }
  .bot-msg { 
    text-align: left; 
    background: #f1f3f4;
    color: #333;
    padding: 8px 12px; 
    margin: 5px 0;
    border-radius: 15px 15px 15px 5px;
    max-width: 80%;
  }
  .input-group {
    display: flex;
    gap: 10px;
    margin-top: 10px;
  }
  #question { 
    flex: 1;
    padding: 10px; 
    border: 1px solid #ddd;
    border-radius: 20px;
    font-size: 16px;
  }
  #sendBtn {
    padding: 10px 20px; 
    background: #007bff;
    color: white;
    border: none; 
    border-radius: 20px; 
    cursor: pointer;
    font-size: 16px;
  }
  #sendBtn:disabled { 
    background: #6c757d; 
    cursor: not-allowed; 
  }
</style>
</head>
<body>
<div class="container">
  <h2>🤖 PhenBOT Study Companion</h2>
  
  <div id="app-status" class="status">Checking status...</div>
  
  <div id="messages">
    <div class="bot-msg">Hello! I'm PhenBOT. Let me check my systems...</div>
  </div>
  
  <div class="input-group">
    <input type="text" id="question" placeholder="Ask a study question..." />
    <button id="sendBtn" disabled>Send</button>
  </div>
</div>

<script>
async function checkStatus() {
  const statusDiv = document.getElementById('app-status');
  try {
    const response = await fetch('/health');
    const data = await response.json();
    
    if (data.groq_available && data.api_key_present) {
      statusDiv.textContent = '✅ All systems operational!';
      statusDiv.className = 'status success';
      document.getElementById('sendBtn').disabled = false;
    } else if (!data.groq_available) {
      statusDiv.textContent = '❌ Groq library not available';
      statusDiv.className = 'status error';
    } else if (!data.api_key_present) {
      statusDiv.textContent = '⚠️ API key not configured';
      statusDiv.className = 'status warning';
    }
  } catch (error) {
    statusDiv.textContent = '❌ Cannot connect to server';
    statusDiv.className = 'status error';
  }
}

document.getElementById('question').addEventListener('input', (e) => {
  const sendBtn = document.getElementById('sendBtn');
  const hasGroq = document.querySelector('.status.success') !== null;
  sendBtn.disabled = !e.target.value.trim() || !hasGroq;
});

async function sendQuestion() {
  const question = document.getElementById('question').value.trim();
  if (!question) return;
  
  const messages = document.getElementById('messages');
  const userDiv = document.createElement('div');
  userDiv.className = 'user-msg';
  userDiv.textContent = question;
  messages.appendChild(userDiv);
  
  document.getElementById('question').value = '';
  document.getElementById('sendBtn').disabled = true;
  
  const thinkingDiv = document.createElement('div');
  thinkingDiv.className = 'bot-msg';
  thinkingDiv.textContent = '🤔 Thinking...';
  messages.appendChild(thinkingDiv);
  messages.scrollTop = messages.scrollHeight;
  
  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question})
    });
    
    const data = await response.json();
    messages.removeChild(thinkingDiv);
    
    const botDiv = document.createElement('div');
    botDiv.className = 'bot-msg';
    botDiv.textContent = data.answer || data.error || 'No response';
    messages.appendChild(botDiv);
    
  } catch (error) {
    messages.removeChild(thinkingDiv);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'bot-msg';
    errorDiv.textContent = 'Error: ' + error.message;
    messages.appendChild(errorDiv);
  }
  
  messages.scrollTop = messages.scrollHeight;
}

document.getElementById('sendBtn').addEventListener('click', sendQuestion);
document.getElementById('question').addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !document.getElementById('sendBtn').disabled) {
    sendQuestion();
  }
});

window.onload = checkStatus;
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
        'api_key_present': bool(GROQ_API_KEY) if GROQ_AVAILABLE else False,
        'port': os.environ.get('PORT', 'not set'),
        'python_path': os.sys.path[0] if hasattr(os, 'sys') else 'unknown'
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        if not GROQ_AVAILABLE:
            return jsonify({'error': 'Groq library not available. Check requirements.txt and deployment logs.'})
        
        if not groq_client:
            return jsonify({'error': 'Groq API key not configured. Please set GROQ_API_KEY environment variable.'})
        
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please provide a question.'})

        response = groq_client.chat.completions.create(
            messages=[{
                "role": "user", 
                "content": f"You are PhenBOT, a helpful study companion. Answer this question clearly and concisely: {question}"
            }],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=300
        )
        
        return jsonify({'answer': response.choices[0].message.content})
        
    except Exception as e:
        print(f"Error in api_ask: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'})

# Simple test route
@app.route('/test')
def test():
    return jsonify({
        'message': 'Flask app is running!',
        'port': os.environ.get('PORT', 'default'),
        'groq_available': GROQ_AVAILABLE
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
