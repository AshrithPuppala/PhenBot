from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<title>PhenBOT Study Companion</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:sans-serif;background:#f9f9f9;margin:0;padding:24px;}
#main{max-width:640px;background:#fff;margin:0 auto;padding:32px;border-radius:10px;box-shadow:0 0 10px #ddd;}
#messages{height:320px;overflow-y:auto;border:1px solid #ccc;padding:1em;background:#fafafa;margin-bottom:1em;}
.user-msg{text-align:right;color:#4e7be7;}
.bot-msg{text-align:left;color:#333;background:#efefef;border-radius:8px;margin:6px 0;padding:8px;}
#question{width:70%;padding:8px;}
#sendBtn{padding:8px 16px;}
</style>
</head>
<body>
<div id="main">
  <h2>PhenBOT Study Companion</h2>
  <div id="messages"></div>
  <input id="question" placeholder="Ask a study question..." autocomplete="off">
  <button id="sendBtn" disabled>Send</button>
</div>
<script>
const q=document.getElementById('question');
const b=document.getElementById('sendBtn');
const m=document.getElementById('messages');
q.oninput=()=>b.disabled=!q.value.trim();
b.onclick=send;
q.onkeypress=e=>{if(e.key==='Enter'&&!b.disabled)send();}
function append(type,txt){let d=document.createElement('div');d.className=type;d.innerText=txt;m.appendChild(d);m.scrollTop=m.scrollHeight;}
async function send(){
 let text=q.value.trim(); if(!text)return;
 append('user-msg',text); q.value=''; b.disabled=1; append('bot-msg','Thinking...');
 let rm=m.querySelector('.bot-msg:last-child');
 try{
  let r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text})});
  let j=await r.json();
  rm.remove();
  append('bot-msg',j.answer||j.error||'No response.');
 }catch(e){
  rm.remove();
  append('bot-msg','Server error.');
 }
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/ask", methods=["POST"])
def ask():
    if not groq_client: return jsonify({"error":"Misconfigured server (no API key)"}), 500
    data = request.get_json(silent=True) or {}
    q = data.get("question","").strip()
    if not q: return jsonify({"error":"Please enter a question."})
    prompt = f"You are PhenBOT, an academic assistant. Be concise yet clear.\nQuestion: {q}"
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role":"user","content":prompt}],
            model="llama-3.1-8b-instant", temperature=0.7, max_tokens=500
        )
        return jsonify({"answer":res.choices[0].message.content})
    except Exception as e:
        return jsonify({"error":f"AI call error: {e}"}),500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
