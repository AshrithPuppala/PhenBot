from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os

app = Flask(__name__)

# Get API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# HTML template embedded in Python (since Vercel has issues with static files)
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
    background: #f9f9f9; 
    line-height: 1.6;
  }
  #chatbox { 
    max-width: 700px; 
    margin: 0 auto; 
    padding: 15px; 
    background: white; 
    border-radius: 8px; 
    box-shadow: 0 0 10px #ddd; 
  }
  #messages { 
    height: 400px; 
    overflow-y: auto; 
    border: 1px solid #ddd; 
    padding: 10px; 
    margin-bottom: 10px; 
    background: #fafafa; 
    border-radius: 5px;
  }
  .user-msg { 
    text-align: right; 
    color: #1a73e8; 
    padding: 8px 12px; 
    margin: 5px 0; 
    background: #e3f2fd;
    border-radius: 15px 15px 5px 15px;
    max-width: 80%;
    margin-left: auto;
  }
  .bot-msg { 
    text-align: left; 
    color: #333; 
    padding: 8px 12px; 
    margin: 5px 0; 
    background: #efefef; 
    border-radius: 15px 15px 15px 5px;
    max-width: 80%;
  }
  .input-container {
    display: flex;
    gap: 10px;
  }
  #question { 
    flex: 1;
    padding: 12px; 
    font-size: 16px;
    border: 1px solid #ddd;
    border-radius: 25px;
    outline: none;
  }
  #question:focus {
    border-color: #1a73e8;
    box-shadow: 0 0 5px rgba(26, 115, 232, 0.3);
  }
  #sendBtn { 
    padding: 12px 20px; 
    font-size: 16px; 
    background: #1a73e8; 
    color: white; 
    border: none; 
    border-radius: 25px; 
    cursor: pointer;
    transition: background 0.3s;
  }
  #sendBtn:hover:not(:disabled) {
    background: #1557b0;
  }
  #sendBtn:disabled { 
    background: #9bbbf9; 
    cursor: not-allowed; 
  }
  .loading {
    color: #666;
    font-style: italic;
  }
  .error {
    color: #d32f2f;
    background: #ffebee;
    border-left: 4px solid #d32f2f;
  }
</style>
</head>
<body>
<div id="chatbox">
  <h2>🤖 PhenBOT Study Companion</h2>
  <div id="messages">
    <div class="bot-msg">Hello! I'm PhenBOT, your AI study companion. Ask me any academic question and I'll help you learn!</div>
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
  
  // Enable/disable send button based on input
  questionInput.addEventListener('input', () => {
    sendBtn.disabled = questionInput.value.trim() === '';
  });

  async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;

    // Add user message
    appendMessage('user-msg', question);
    questionInput.value = '';
    sendBtn.disabled = true;

    // Show loading message
    const loadingDiv = appendMessage('bot-msg loading', 'Thinking...');

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
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.answer) {
        appendMessage('bot-msg', data.answer);
      } else {
        appendMessage('bot-msg error', 'Sorry, no answer was returned.');
      }
    } catch (error) {
      // Remove loading message if still there
      if (loadingDiv && loadingDiv.parentNode) {
        loadingDiv.parentNode.removeChild(loadingDiv);
      }
      
      appendMessage('bot-msg error', `Error: ${error.message}`);
      console.error('Error:', error);
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

  // Focus on input when page loads
  questionInput.focus();
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
            return jsonify({'answer': 'API configuration error. Please check server logs.'})

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
        print(f"Error in api_ask: {str(e)}")
        return jsonify({'answer': f'Sorry, I encountered an error: {str(e)}'}), 500

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'groq_configured': groq_client is not None})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
