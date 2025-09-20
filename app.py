# app.py  -- improved, robust Groq initialization and clearer errors
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

# (For brevity in this snippet, paste your existing HTML_TEMPLATE here)

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

# Do NOT call initialize_groq() at import time if you want absolute safety,
# but it's okay to attempt to initialize here as we handle errors gracefully.
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
    print(f"Starting local dev server on :{port} (GROQ_AVAILABLE={GROQ_AVAILABLE})")
    app.run(host='0.0.0.0', port=port, debug=False)

