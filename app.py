from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os

app = Flask(__name__)

# Get API key from environment - Railway sets this automatically
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"API Key present: {bool(GROQ_API_KEY)}")  # Debug log

try:
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    if groq_client:
        print("Groq client initialized successfully")
    else:
        print("ERROR: Groq client not initialized - missing API key")
except Exception as e:
    print(f"ERROR initializing Groq client: {e}")
    groq_client = None

# HTML template embedded in Python
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PhenBOT Study Companion</title>
<style>
  body { 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    margin: 20px; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    line-height: 1.6;
  }
  #chatbox { 
    max-width: 700px; 
    margin: 20px auto; 
    padding: 20px; 
    background: white; 
    border-radius: 15px; 
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  }
  h2 {
    text-align: center;
    color: #333;
    margin-bottom: 20px;
    font-size: 28px;
  }
  #messages { 
    height: 400px; 
    overflow-y: auto; 
    border: 1px solid #e0e0e0; 
    padding: 15px;
    margin-bottom: 15px; 
    background: #fafafa;
    border-radius: 10px;
  }
  .user-msg { 
    text-align: right; 
    color: #1a73e8; 
    padding: 10px 15px; 
    margin: 8px 0; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 20px 20px 5px 20px;
    max-width: 80%;
    margin-left: auto;
    word-wrap: break-word;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  }
  .bot-msg { 
    text-align: left; 
    color: #333; 
    padding: 10px 15px; 
    margin: 8px 0;
    background: #f0f0f0; 
    border-radius: 20px 20px 20px 5px;
    max-width: 80%;
    word-wrap: break-word;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  }
  .input-container {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  #question { 
    flex: 1;
    padding: 15px 20px; 
    font-size: 16px;
    border: 2px solid #e0e0e0;
    border-radius: 25px;
    outline: none;
    transition: border-color 0.3s;
  }
  #question:focus {
    border-color: #667eea;
    box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
  }
  #sendBtn {
    padding: 15px 25px; 
    font-size: 16px; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none; 
    border-radius: 25px; 
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    font-weight: bold;
  }
  #sendBtn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
  }
  #sendBtn:disabled { 
    background: #cccccc; 
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  .loading {
    color: #666;
    font-style: italic;
    animation: pulse 1.5s infinite;
  }
  .error {
    color: #d32f2f;
    background: #ffebee !important;
    border-left: 4px solid #d32f2f;
  }
  .welcome {
    background: linear-gradient(135deg, #4caf50, #45a049);
    color: white;
    border-radius: 20px 20px 20px 5px;
  }
  .status {
    text-align: center;
    padding: 10px;
    margin: 10px 0;
    border-radius: 10px;
    font-size: 14px;
  }
  .status.connected {
    background: #e8f5e8;
    color: #2e7d32;
    border: 1px solid #4caf50;
  }
  .status.error {
    background: #ffebee;
    color: #d32f2f;
    border: 1px solid #f44336;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  @media (max-width: 600px) {
    body { margin: 10px; }
    #chatbox { padding: 15px; margin: 10px auto; }
    .input-container { flex-direction: column; }
    #question { margin-bottom: 10px; }
  }
</style>
</head>
<body>
<div id="chatbox">
  <h2>🤖 PhenBOT Study Companion</h2>
  <div id="status" class="status">Checking connection...</div>
  <div id="messages">
    <div class="bot-msg welcome">Hello! I'm PhenBOT, your AI study companion. Ask me any academic question and I'll help you learn!</div>
  </div>
  <div class="input-container">
    <input type="text" id="question" placeholder="Ask a study question..." autocomplete="off" />
    <button id="sendBtn" disabled>Send</button>
  </div>
</div>

<script>
  const messages = document.getElementById('messages');
  const questionInput = document.getElementById('question');
  const sendBtn = document.getElementById('sendBtn');
  const statusDiv = document.getElementById('status');
  
  // Check API status on load
  async function checkStatus() {
    try {
      const response = await fetch('/health');
      const data = await response.json();
      
      if (data.groq_configured) {
        statusDiv.textContent = '✅ Connected and ready!';
        statusDiv.className = 'status connected';
        questionInput.disabled = false;
      } else {
        statusDiv.textContent = '❌ API key not configured';
        statusDiv.className = 'status error';
        questionInput.disabled = true;
      }
    } catch (error) {
      statusDiv.textContent = '❌ Server connection failed';
      statusDiv.className = 'status error';
      questionInput.disabled = true;
    }
  }
  
  // Enable/disable send button based on input
  questionInput.addEventListener('input', () => {
    sendBtn.disabled = questionInput.value.trim() === '' || questionInput.disabled;
  });

  async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    // Add user message
    appendMessage('user-msg', question);
    questionInput.value = '';
    sendBtn.disabled = true;

    // Show loading message
    const loadingDiv = appendMessage('bot-msg loading', '🤔 Thinking...');

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question })
      });

      // Remove loading message
      if (loadingDiv && loadingDiv.parentNode) {
        loadingDiv.parentNode.removeChild(loadingDiv);
      }

      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.answer) {
        appendMessage('bot-msg', data.answer);
      } else if (data.error) {
        appendMessage('bot-msg error', `Error: ${data.error}`);
      } else {
        appendMessage('bot-msg error', 'Sorry, no answer was returned.');
      }
    } catch (error) {
      // Remove loading message if still there
      if (loadingDiv && loadingDiv.parentNode) {
        loadingDiv.parentNode.removeChild(loadingDiv);
      }
      
      let errorMessage = 'Error contacting server.';
      if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Network error. Please check your connection.';
      } else if (error.message) {
        errorMessage = `Error: ${error.message}`;
      }
      
      appendMessage('bot-msg error', errorMessage);
      console.error('Detailed error:', error);
    }
  }

  function appendMessage(className, text) {
    const div = document.createElement('div');
    div.className = className;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  // Event listeners
  sendBtn.addEventListener('click', sendQuestion);
  
  questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !sendBtn.disabled) {
      sendQuestion();
    }
  });

  // Initialize
  window.addEventListener('load', () => {
    checkStatus();
    questionInput.focus();
  });
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'answer': 'Please enter a question.'})

        if not groq_client:
            return jsonify({'error': 'GROQ_API_KEY environment variable not set or invalid. Please check Railway environment variables.'})

        # Create a more specific prompt
        prompt = f"""You are PhenBOT, a helpful academic study companion. Provide clear, educational answers to student questions.

Question: {question}

Please provide a comprehensive but concise answer that helps the student understand the topic."""

        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        return jsonify({'answer': answer})
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        print(f"Error in api_ask: {str(e)}")
        return jsonify({'error': error_msg}), 500

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'groq_configured': groq_client is not None,
        'api_key_present': bool(GROQ_API_KEY)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
