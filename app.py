from flask import Flask, request, jsonify, render_template_string
import os
import sys

app = Flask(__name__)

# Globals for Groq client and status
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    try:
        from groq import Groq
    except ImportError as e:
        GROQ_ERROR = "Groq library not installed"
        print(GROQ_ERROR, file=sys.stderr)
        return
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        GROQ_ERROR = "Groq API key missing in environment variables"
        print(GROQ_ERROR, file=sys.stderr)
        return
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {e}"
        print(GROQ_ERROR, file=sys.stderr)

# Initialize Groq client at startup
initialize_groq()

# Embedded complete UI HTML template string with your styles and scripts
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PhenBOT Study Companion</title>
  <style>
    /* Your full CSS styles from current file */
    body { font-family: Arial, sans-serif; background: #f9f9f9; margin: 0; padding: 24px; }
    #main { max-width: 640px; background: #fff; margin: 40px auto; padding: 32px; border-radius: 10px; box-shadow: 0 0 10px #ddd; }
    #messages { height: 320px; overflow-y: auto; border: 1px solid #ccc; padding: 1em; background: #fafafa; margin-bottom: 1em; }
    .user-msg { text-align: right; color: #1a73e8; margin: 5px 0; }
    .bot-msg { text-align: left; color: #333; background: #efefef; border-radius: 8px; padding: 8px; margin: 5px 0; display: inline-block; }
    #question { width: 70%; padding: 8px; }
    #sendBtn { padding: 8px 16px; }
  </style>
</head>
<body>
  <div id="main">
    <h2>PhenBOT Study Companion</h2>
    <div id="messages"></div>
    <input id="question" placeholder="Ask a study question..." autocomplete="off" />
    <button id="sendBtn" disabled>Send</button>
  </div>
  <script>
    const q = document.getElementById('question');
    const b = document.getElementById('sendBtn');
    const m = document.getElementById('messages');
    q.oninput = () => b.disabled = !q.value.trim();
    b.onclick = send;
    q.onkeypress = e => { if (e.key === 'Enter' && !b.disabled) send(); };
    function append(type, text) {
      let d = document.createElement('div');
      d.className = type;
      d.innerText = text;
      m.appendChild(d);
      m.scrollTop = m.scrollHeight;
    }
    async function send() {
      let text = q.value.trim();
      if (!text) return;
      append('user-msg', text);
      q.value = '';
      b.disabled = true;
      append('bot-msg', 'Thinking...');
      let nds = m.querySelector('.bot-msg:last-child');
      try {
        let r = await fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text })
        });
        let j = await r.json();
        nds.remove();
        append('bot-msg', j.answer || j.error || 'No response.');
      } catch (e) {
        nds.remove();
        append('bot-msg', 'Server error.');
      }
      b.disabled = false;
    }
  </script>
</body>
</html>
"""

# Routes for UI and API
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/ask", methods=["POST"])
def api_ask():
    if not GROQ_AVAILABLE:
        return jsonify({"error": f"Groq not initialized: {GROQ_ERROR}"}), 500
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Please enter a question."}), 400
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are PhenBOT, a helpful academic assistant."},
                {"role": "user", "content": question}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500,
        )
        return jsonify({"answer": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": f"Groq API error: {str(e)}"}), 500

# Optional health check (useful for monitoring)
@app.route("/health")
def health():
    return jsonify({
        "groq_available": GROQ_AVAILABLE,
        "api_key_present": bool(os.environ.get("GROQ_API_KEY")),
        "groq_error": GROQ_ERROR,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "status": "healthy" if GROQ_AVAILABLE else "error"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
