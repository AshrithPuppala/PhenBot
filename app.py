# app.py
from flask import Flask, request, jsonify, render_template_string
import os
import sys

# Import Groq library at the top for standard practice
from groq import Groq, GroqError

app = Flask(__name__)

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initializes the Groq client and checks for necessary environment variables."""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    api_key = os.environ.get('GROQ_API_KEY')
    
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY environment variable is missing."
        print(GROQ_ERROR, file=sys.stderr)
        return
    
    try:
        # The key to fixing the error: Initialize without any 'proxies' argument.
        # This is the correct way to initialize the client with recent versions of the Groq library.
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully.")
    except GroqError as e:
        # Catch specific Groq API errors for better reporting
        GROQ_ERROR = f"Groq API client failed to initialize: {e}"
        print(GROQ_ERROR, file=sys.stderr)
    except Exception as e:
        GROQ_ERROR = f"An unexpected error occurred during Groq initialization: {e}"
        print(GROQ_ERROR, file=sys.stderr)

# Call the initialization function when the app starts
initialize_groq()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang='en'><head><meta charset='UTF-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>PhenBOT Study Companion</title>
<style>
body { font-family: Arial, sans-serif; background: #f9f9f9; margin: 0; padding: 24px; }
#main { max-width: 640px; background: #fff; margin: 40px auto; padding: 32px; border-radius: 10px; box-shadow: 0 0 10px #ddd; }
#messages { height: 320px; overflow-y: auto; border: 1px solid #ccc; padding: 1em; background: #fafafa; margin-bottom: 1em; }
.user-msg { text-align: right; color: #1a73e8; }
.bot-msg { text-align: left; color: #333; background: #efefef; border-radius: 8px; padding: 8px; }
#question { width: 70%; padding: 8px; } #sendBtn { padding: 8px 16px; }
</style>
</head><body>
<div id='main'>
<h2>PhenBOT Study Companion</h2>
<div id='messages'></div>
<input id='question' placeholder='Ask a study question...' autocomplete='off'/>
<button id='sendBtn' disabled>Send</button>
</div>
<script>
const q=document.getElementById('question');
const b=document.getElementById('sendBtn');
const m=document.getElementById('messages');
q.oninput=()=>b.disabled=!q.value.trim();
b.onclick=send;
q.onkeypress=e=>{if(e.key==='Enter'&&!b.disabled)send();}
function append(type,text){let d=document.createElement('div');d.className=type;d.innerText=text;m.appendChild(d);m.scrollTop=m.scrollHeight;}
async function send(){
 let text=q.value.trim(); if(!text)return;
 append('user-msg',text); q.value=''; b.disabled=1; append('bot-msg','Thinking...');
 let nds=m.querySelector('.bot-msg:last-child');
 try{
  let r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text})});
  let j=await r.json();
  nds.remove();
  append('bot-msg',j.answer||j.error||'No response.');
 }catch(e){
  nds.remove();
  append('bot-msg','Server error.');
 }
}
</script>
</body></html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'groq_error': GROQ_ERROR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'status': 'healthy' if GROQ_AVAILABLE else 'error',
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    if not GROQ_AVAILABLE:
        return jsonify({'error': f'Groq not available: {GROQ_ERROR}'}), 500
    data = request.get_json() or {}
    question = data.get('question','').strip()
    if not question:
        return jsonify({'error': 'Please enter a question.'}), 400
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': 'You are PhenBOT, a helpful academic assistant.'},
                {'role': 'user', 'content': question}
            ],
            model='llama-3.1-8b-instant', temperature=0.7, max_tokens=500
        )
        return jsonify({'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f'Groq API error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
