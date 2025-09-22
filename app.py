# ---------- Part A of 3 ----------
import os
import re
import io
import json
import uuid
import traceback
from datetime import datetime
from functools import wraps

from flask import (
    Flask, request, jsonify, render_template_string,
    redirect, url_for, flash, session, send_file
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Attempt optional AI SDK imports (Groq or OpenAI)
GROQ_AVAILABLE = False
OPENAI_AVAILABLE = False
groq_client = None
openai = None

try:
    import groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# PDF extraction
try:
    import PyPDF2
except Exception as e:
    raise RuntimeError("PyPDF2 is required. pip install PyPDF2") from e

# ------------------------
# HTML TEMPLATES (keep these at top so routes can use them)
# ------------------------

LOGIN_HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PhenBOT - Login</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    /* minimal login styles */
    body{font-family:Inter,Roboto,Arial;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#667eea,#764ba2)}
    .card{background:#fff;padding:28px;border-radius:14px;box-shadow:0 20px 50px rgba(0,0,0,0.15);width:360px}
    h1{margin:0 0 8px;font-size:22px;color:#333}
    .muted{color:#666;font-size:14px;margin-bottom:18px}
    label{display:block;margin-bottom:6px;color:#333;font-weight:600}
    input{width:100%;padding:10px;border-radius:8px;border:1px solid #e6edf3;margin-bottom:12px}
    button{width:100%;padding:10px;border-radius:10px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-weight:700;cursor:pointer}
    .links{margin-top:12px;text-align:center}
    .flash{margin-bottom:10px;padding:8px;border-radius:8px}
    .flash.error{background:#ffecec;color:#9b1a1a}
    .flash.success{background:#e8ffef;color:#056b2f}
  </style>
</head>
<body>
  <div class="card">
    <h1>PhenBOT</h1>
    <div class="muted">Advanced Study Companion — sign in</div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, msg in messages %}
          <div class="flash {{ 'error' if category == 'error' else 'success' }}">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST">
      <label for="username">Username</label>
      <input id="username" name="username" required>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" required>
      <button type="submit">Sign in</button>
    </form>
    <div class="links"><a href="{{ url_for('register') }}">Create an account</a></div>
  </div>
</body>
</html>
'''

REGISTER_HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PhenBOT - Register</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{font-family:Inter,Roboto,Arial;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#667eea,#764ba2)}
    .card{background:#fff;padding:28px;border-radius:14px;box-shadow:0 20px 50px rgba(0,0,0,0.15);width:360px}
    h1{margin:0 0 8px;font-size:22px;color:#333}
    .muted{color:#666;font-size:14px;margin-bottom:18px}
    label{display:block;margin-bottom:6px;color:#333;font-weight:600}
    input{width:100%;padding:10px;border-radius:8px;border:1px solid #e6edf3;margin-bottom:12px}
    button{width:100%;padding:10px;border-radius:10px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-weight:700;cursor:pointer}
    .links{margin-top:12px;text-align:center}
    .flash{margin-bottom:10px;padding:8px;border-radius:8px}
    .flash.error{background:#ffecec;color:#9b1a1a}
    .flash.success{background:#e8ffef;color:#056b2f}
  </style>
</head>
<body>
  <div class="card">
    <h1>Create account</h1>
    <div class="muted">Sign up for PhenBOT</div>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, msg in messages %}
          <div class="flash {{ 'error' if category == 'error' else 'success' }}">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    <form method="POST">
      <label for="username">Username</label>
      <input id="username" name="username" required minlength="3">
      <label for="password">Password</label>
      <input id="password" name="password" type="password" required minlength="6">
      <button type="submit">Create account</button>
    </form>
    <div class="links"><a href="{{ url_for('login') }}">Have an account? Sign in</a></div>
  </div>
</body>
</html>
'''

# Main app UI (large). This template corresponds to the comprehensive frontend you provided earlier.
# For brevity in this message, I keep the earlier long HTML you showed (it contains CSS + JS).
# I will include the long template exactly; if you want custom trimming tell me later.
MAIN_APP_HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>PhenBOT - AI Study Assistant</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
/* (Full CSS from your earlier main template - condensed but intact) */
:root{--primary-bg:#f5f7fa;--card:#fff;--muted:#666}
*{box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);margin:0}
.header{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:1rem 2rem;position:fixed;top:0;left:0;right:0;z-index:1000}
.header-content{max-width:1400px;margin:auto;display:flex;justify-content:space-between;align-items:center}
.main-container{display:flex;margin-top:80px;min-height:calc(100vh - 80px)}
.sidebar{width:300px;background:var(--card);padding:2rem 1rem;box-shadow:4px 0 20px rgba(0,0,0,0.08);overflow:auto}
.chat-area{flex:1;display:flex;flex-direction:column;background:var(--card);margin:1rem;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.08);overflow:hidden}
.chat-header{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:1rem 1.5rem;display:flex;justify-content:space-between;align-items:center}
.chat-messages{flex:1;padding:1.5rem;overflow-y:auto;background:#f8fafc}
.message{display:flex;gap:12px;margin-bottom:12px}
.avatar{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700}
.avatar.bot{background:linear-gradient(135deg,#10b981,#06b6d4)}
.avatar.user{background:linear-gradient(135deg,#667eea,#764ba2)}
.message-content{padding:12px;border-radius:12px;max-width:78%;line-height:1.45}
.message-user .message-content{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.message-bot .message-content{background:#fff;border:1px solid #e1e5e9}
.chat-input{padding:1rem;border-top:1px solid #e6edf3;background:#fff}
.input-field{width:100%;min-height:60px;padding:12px;border-radius:10px;border:1px solid #e6edf3;resize:none}
.controls-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:12px}
.btn{padding:8px 12px;border-radius:8px;border:none;cursor:pointer}
.btn-primary{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.file-drop-zone{border:2px dashed #667eea;padding:12px;border-radius:10px;text-align:center;background:#f8fafc;cursor:pointer}
.toast{position:fixed;right:20px;bottom:20px;background:#111827;color:#fff;padding:10px 14px;border-radius:8px;opacity:0;transform:translateY(12px);transition:all .25s}
.toast.show{opacity:1;transform:none}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:2000;align-items:center;justify-content:center;padding:1rem}
.modal-overlay.show{display:flex}
.modal{background:#fff;border-radius:12px;max-width:900px;width:100%;max-height:90vh;overflow:auto;padding:12px}
@media (max-width:768px){.main-container{flex-direction:column}.sidebar{width:100%}}
</style>
</head>
<body>
<div class="header">
  <div class="header-content">
    <div class="logo">🤖 PhenBOT</div>
    <div class="user-info">
      <span class="user-name">Welcome, {{ username }}!</span>
      <a href="{{ url_for('logout') }}" class="btn" style="background:rgba(255,255,255,0.15);color:#fff;border-radius:8px;padding:8px 10px;text-decoration:none">Logout</a>
    </div>
  </div>
</div>

<div class="main-container">
  <div class="sidebar">
    <div style="margin-bottom:18px">
      <strong>🍅 Focus Timer</strong>
      <div style="margin-top:10px;background:linear-gradient(135deg,#ff6b6b,#ee5a24);padding:12px;border-radius:10px;color:#fff;text-align:center">
        <div id="timerDisplay" style="font-weight:800;font-size:20px">25:00</div>
        <div style="margin-top:8px">
          <button class="btn" id="timerStartBtn">Start</button>
          <button class="btn" id="timerPauseBtn">Pause</button>
          <button class="btn" id="timerResetBtn">Reset</button>
        </div>
      </div>
    </div>

    <div style="margin-bottom:18px">
      <strong>📊 Today's Stats</strong>
      <div style="background:#fff;padding:12px;border-radius:8px;margin-top:8px">
        <div style="display:flex;justify-content:space-between"><div>Questions</div><div id="statQuestions">0</div></div>
        <div style="display:flex;justify-content:space-between"><div>Sessions</div><div id="statSessions">0</div></div>
        <div style="display:flex;justify-content:space-between"><div>Flashcards</div><div id="statFlashcards">0</div></div>
      </div>
    </div>

    <div>
      <strong>⚡ Quick Actions</strong>
      <div style="display:flex;flex-direction:column;gap:8px;margin-top:8px">
        <button class="btn btn-primary" id="clearChatBtn">Clear Chat</button>
        <button class="btn" id="exportChatBtn">Export Chat</button>
        <button class="btn" id="openFlashcardModal">Open Flashcards</button>
      </div>
    </div>
  </div>

  <div class="chat-area">
    <div class="chat-header">
      <div style="display:flex;gap:12px;align-items:center"><div style="font-weight:700">AI Study Assistant</div></div>
      <div id="aiStatus">AI Online</div>
    </div>

    <div class="chat-messages" id="chatMessages">
      <div class="message message-bot"><div class="avatar bot">B</div><div><div class="message-content">Hello! I'm PhenBOT — your AI study companion.</div><div class="message-meta">Just now</div></div></div>
    </div>

    <div class="chat-input">
      <div class="controls-row">
        <div>
          <label>Attach PDF</label>
          <div id="dropZone" class="file-drop-zone">Drop PDF here or <button class="btn" id="selectFileBtn">Select File</button></div>
          <input id="fileInput" type="file" accept="application/pdf" style="display:none">
          <div id="fileInfo" style="display:none;margin-top:8px;padding:8px;background:#e0f2fe;border-radius:8px"></div>
          <div style="margin-top:8px">
            <button class="btn btn-primary" id="summarizeFileBtn">Summarize File</button>
            <button class="btn" id="generateFlashcardsBtn">Generate Flashcards</button>
          </div>
        </div>

        <div>
          <label>Modes & Length</label>
          <div style="display:flex;flex-direction:column;gap:8px">
            <select id="chatMode" style="padding:8px;border-radius:8px"><option value="normal">Normal</option><option value="analogy">Analogy</option><option value="quiz">Quiz</option><option value="teach">Teaching</option><option value="socratic">Socratic</option><option value="explain">ELI5</option></select>
            <select id="responseLength" style="padding:8px;border-radius:8px"><option value="short">Short</option><option value="normal" selected>Normal</option><option value="detailed">Detailed</option></select>
            <button class="btn" id="voiceBtn">🎙️</button>
          </div>
        </div>
      </div>

      <div style="display:flex;gap:12px;align-items:flex-end">
        <textarea id="messageInput" class="input-field" placeholder="Ask me anything — Enter to send"></textarea>
        <div style="display:flex;flex-direction:column;gap:8px">
          <button class="btn btn-primary" id="sendBtn">Send</button>
          <button class="btn" id="moreBtn">⋯</button>
        </div>
      </div>
    </div>

  </div>
</div>

<!-- Flashcard modal -->
<div id="flashcardModal" class="modal-overlay" aria-hidden="true">
  <div class="modal">
    <div style="display:flex;justify-content:space-between;align-items:center"><h3>Flashcard Library</h3><button id="closeFlashcardModal">✕</button></div>
    <div style="margin-top:12px">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
        <input id="flashTopic" placeholder="Topic (optional)" style="flex:1;padding:8px;border-radius:6px;border:1px solid #e6edf3">
        <select id="flashDifficulty" style="padding:8px;border-radius:6px"><option value="easy">Easy</option><option value="medium" selected>Medium</option><option value="hard">Hard</option></select>
        <button class="btn btn-primary" id="generateTopicFlashcards">Generate</button>
      </div>
      <div id="flashcardsContainer"></div>
    </div>
  </div>
</div>

<div id="toast" class="toast" role="status" aria-live="polite"></div>

<script>
/* Frontend JS: chat, pdf upload, flashcards, pomodoro, voice, localStorage; uses endpoints defined in server */
(function(){
  const chatMessages = document.getElementById('chatMessages');
  const messageInput = document.getElementById('messageInput');
  const sendBtn = document.getElementById('sendBtn');
  const chatMode = document.getElementById('chatMode');
  const responseLength = document.getElementById('responseLength');
  const voiceBtn = document.getElementById('voiceBtn');
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileInfo = document.getElementById('fileInfo');
  const summarizeFileBtn = document.getElementById('summarizeFileBtn');
  const generateFlashcardsBtn = document.getElementById('generateFlashcardsBtn');
  const toast = document.getElementById('toast');
  const timerDisplay = document.getElementById('timerDisplay');
  const timerStartBtn = document.getElementById('timerStartBtn');
  const timerPauseBtn = document.getElementById('timerPauseBtn');
  const timerResetBtn = document.getElementById('timerResetBtn');
  const statQuestions = document.getElementById('statQuestions');
  const statSessions = document.getElementById('statSessions');
  const statFlashcards = document.getElementById('statFlashcards');
  const clearChatBtn = document.getElementById('clearChatBtn');
  const exportChatBtn = document.getElementById('exportChatBtn');
  const openFlashcardModal = document.getElementById('openFlashcardModal');
  const flashcardModal = document.getElementById('flashcardModal');
  const closeFlashcardModal = document.getElementById('closeFlashcardModal');
  const generateTopicFlashcards = document.getElementById('generateTopicFlashcards');
  const flashcardsContainer = document.getElementById('flashcardsContainer');
  const flashTopic = document.getElementById('flashTopic');
  const flashDifficulty = document.getElementById('flashDifficulty');
  const selectFileBtn = document.getElementById('selectFileBtn');

  let stats = {questions:0,sessions:0,flashcards:0};
  let voiceRec = null;
  let isRecording=false;
  let pomodoroSeconds = 25*60;
  let pomodoroInterval = null;
  let pomodoroRunning=false;
  let inBreak=false;

  function showToast(msg, t=3000){ toast.textContent = msg; toast.classList.add('show'); setTimeout(()=>toast.classList.remove('show'), t); }

  function appendMessage(role, text){
    const node = document.createElement('div');
    node.className = 'message ' + (role==='user'?'message-user':'message-bot');
    const avatar = document.createElement('div');
    avatar.className = 'avatar ' + (role==='user'?'user':'bot');
    avatar.textContent = role==='user'?'U':'B';
    const contentWrap = document.createElement('div');
    const content = document.createElement('div'); content.className='message-content'; content.innerText=text;
    const meta = document.createElement('div'); meta.className='message-meta'; meta.innerText=new Date().toLocaleString();
    contentWrap.appendChild(content); contentWrap.appendChild(meta);
    node.appendChild(avatar); node.appendChild(contentWrap);
    chatMessages.appendChild(node); chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function sendChat(){ 
    const txt = messageInput.value.trim(); if(!txt) return;
    appendMessage('user', txt); messageInput.value='';
    stats.questions++; saveStats(); updateStatsUI();
    const indicator = document.createElement('div'); indicator.className='message message-bot'; indicator.innerHTML='<div class="avatar bot">B</div><div><div class="message-content">...</div><div class="message-meta">Thinking...</div></div>'; chatMessages.appendChild(indicator); chatMessages.scrollTop = chatMessages.scrollHeight;
    try {
      const res = await fetch('/api/chat', {method:'POST',headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:txt, mode:chatMode.value, length:responseLength.value})});
      const data = await res.json();
      indicator.remove();
      if(data.error){ appendMessage('bot','Error: '+data.error); showToast('AI error'); }
      else{ appendMessage('bot', data.reply || data.answer || '[no reply]'); if(window.speechSynthesis) speechSynthesis.speak(new SpeechSynthesisUtterance(data.reply || data.answer || ''));}
    } catch(e){ indicator.remove(); appendMessage('bot','Network error: '+e.message); }
  }

  sendBtn.addEventListener('click', sendChat);
  messageInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendChat(); } });

  // voice
  function initVoice(){
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(!SR){ voiceBtn.style.display='none'; return; }
    voiceRec = new SR(); voiceRec.lang='en-US'; voiceRec.interimResults=false;
    voiceRec.onresult=(ev)=>{ const t = Array.from(ev.results).map(r=>r[0].transcript).join(''); messageInput.value = t; sendChat(); }
    voiceRec.onend=()=>{ isRecording=false; voiceBtn.classList.remove('recording'); }
    voiceRec.onerror=(e)=>{ isRecording=false; voiceBtn.classList.remove('recording'); showToast('Voice error: '+e.error); }
  }
  voiceBtn.addEventListener('click', ()=>{ if(!voiceRec) return; if(!isRecording){ isRecording=true; voiceBtn.classList.add('recording'); voiceRec.start(); } else { isRecording=false; voiceBtn.classList.remove('recording'); voiceRec.stop(); } });
  initVoice();

  // file handling
  dropZone.addEventListener('dragover',(e)=>{e.preventDefault(); dropZone.classList.add('drag-over');});
  dropZone.addEventListener('dragleave',()=>dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop',(e)=>{ e.preventDefault(); dropZone.classList.remove('drag-over'); const f = e.dataTransfer.files && e.dataTransfer.files[0]; if(f) handleSelectedFile(f); });
  selectFileBtn.addEventListener('click', ()=> fileInput.click());
  fileInput.addEventListener('change', (e)=>{ const f = e.target.files && e.target.files[0]; if(f) handleSelectedFile(f); });

  function handleSelectedFile(f){ if(!f.name.toLowerCase().endsWith('.pdf')){ showToast('Only PDF supported'); return; } fileInfo.style.display='block'; fileInfo.textContent = 'Selected: '+f.name+' ('+Math.round(f.size/1024)+' KB)'; fileInput._file = f; }

  async function processFile(action){
    const f = fileInput._file; if(!f){ showToast('Upload PDF first'); return; }
    showToast('Processing file...');
    const form = new FormData(); form.append('file', f); form.append('action', action);
    try {
      const res = await fetch('/api/process_pdf', { method:'POST', body: form });
      const data = await res.json();
      if(data.error){ showToast('Error: '+data.error); appendMessage('bot','PDF error: '+data.error); return; }
      if(action==='summarize'){ appendMessage('bot','PDF Summary:\n'+(data.summary||'[no summary]')); }
      else if(action==='flashcards'){ if(data.flashcards){ renderFlashcards(data.flashcards); stats.flashcards += data.flashcards.length; saveStats(); updateStatsUI(); showToast('Generated flashcards'); } else { appendMessage('bot', JSON.stringify(data)); } }
    } catch(e){ showToast('Network error: '+e.message); }
  }

  summarizeFileBtn.addEventListener('click', ()=> processFile('summarize'));
  generateFlashcardsBtn.addEventListener('click', ()=> processFile('flashcards'));

  // flashcards modal
  document.getElementById('openFlashcardModal').addEventListener('click', ()=>{ flashcardModal.classList.add('show'); flashcardModal.style.display='flex'; });
  closeFlashcardModal.addEventListener('click', ()=>{ flashcardModal.classList.remove('show'); flashcardModal.style.display='none'; });
  document.getElementById('generateTopicFlashcards').addEventListener('click', async ()=>{
    const topic = flashTopic.value.trim(); if(!topic){ showToast('Enter topic'); return; }
    showToast('Generating flashcards...');
    try {
      const res = await fetch('/api/generate_flashcards', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({source_type:'topic', topic, subject:'general', difficulty:flashDifficulty.value, count:8, save_flashcards:false})});
      const data = await res.json();
      if(data.error){ showToast('Error: '+data.error); return; }
      renderFlashcards(data.flashcards||[]);
      stats.flashcards += (data.flashcards||[]).length; saveStats(); updateStatsUI();
    } catch(e){ showToast('Error: '+e.message); }
  });

  function renderFlashcards(cards){
    flashcardsContainer.innerHTML = '';
    (cards||[]).forEach((c,i)=>{
      const el = document.createElement('div');
      el.className='flashcard';
      el.innerHTML = '<div class="flashcard-content"><strong>'+ (c.front||c.question||('Card '+(i+1))) +'</strong><div class="flashcard-hint">'+(c.difficulty||'')+'</div></div>';
      el.addEventListener('click', ()=>{
        if(el.classList.contains('flipped')){ el.classList.remove('flipped'); el.innerHTML = '<div class="flashcard-content"><strong>'+ (c.front||c.question||('Card '+(i+1))) +'</strong><div class="flashcard-hint">'+(c.difficulty||'')+'</div></div>'; }
        else { el.classList.add('flipped'); el.innerHTML = '<div class="flashcard-content"><strong>'+(c.back||c.answer||'Answer')+'</strong></div>'; }
      });
      flashcardsContainer.appendChild(el);
    });
  }

  // clear/export
  clearChatBtn.addEventListener('click', ()=>{ chatMessages.innerHTML=''; appendMessage('bot','Chat cleared.'); localStorage.removeItem('phenbot_conversation'); });
  exportChatBtn.addEventListener('click', ()=>{
    const text = Array.from(chatMessages.querySelectorAll('.message')).map(m=>{ const who = m.classList.contains('message-user')?'User':'Bot'; const content = m.querySelector('.message-content')?.innerText||''; const meta = m.querySelector('.message-meta')?.innerText||''; return who+' ['+meta+']:\\n'+content; }).join('\\n\\n');
    const blob = new Blob([text], {type:'text/plain'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download='phenbot_chat.txt'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); showToast('Chat exported');
  });

  // stats persist
  function loadStats(){ const raw = localStorage.getItem('phenbot_stats'); if(raw) try{ stats = JSON.parse(raw);}catch(e){} updateStatsUI(); }
  function saveStats(){ localStorage.setItem('phenbot_stats', JSON.stringify(stats)); }
  function updateStatsUI(){ statQuestions.innerText = stats.questions||0; statSessions.innerText = stats.sessions||0; statFlashcards.innerText = stats.flashcards||0; }

  // pomodoro
  function formatTime(s){ const m = Math.floor(s/60); const sec = s%60; return String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0'); }
  function startTimer(){ if(pomodoroRunning) return; pomodoroRunning=true; pomodoroInterval = setInterval(()=>{ if(pomodoroSeconds<=0){ clearInterval(pomodoroInterval); pomodoroRunning=false; stats.sessions=(stats.sessions||0)+1; saveStats(); updateStatsUI(); showToast(inBreak?'Break ended':'Focus session finished'); inBreak = !inBreak; pomodoroSeconds = inBreak?5*60:25*60; timerDisplay.innerText = formatTime(pomodoroSeconds); } else { pomodoroSeconds--; timerDisplay.innerText = formatTime(pomodoroSeconds); } },1000); }
  function pauseTimer(){ if(pomodoroInterval) clearInterval(pomodoroInterval); pomodoroRunning=false; }
  function resetTimer(){ if(pomodoroInterval) clearInterval(pomodoroInterval); pomodoroRunning=false; inBreak=false; pomodoroSeconds=25*60; timerDisplay.innerText = formatTime(pomodoroSeconds); }
  timerStartBtn.addEventListener('click', startTimer); timerPauseBtn.addEventListener('click', pauseTimer); timerResetBtn.addEventListener('click', resetTimer);

  // load saved conversation (optional)
  setInterval(()=>{ const nodes = Array.from(chatMessages.querySelectorAll('.message')); const toSave = nodes.map(n=>({role:n.classList.contains('message-user')?'user':'bot', text:n.querySelector('.message-content')?.innerText||'', meta:n.querySelector('.message-meta')?.innerText||''})); localStorage.setItem('phenbot_conversation', JSON.stringify(toSave)); },10000);
  function init(){ loadStats(); const conv = localStorage.getItem('phenbot_conversation'); if(conv) try{ JSON.parse(conv).forEach(m=>appendMessage(m.role,m.text)); }catch(e){} }
  init();

})();
</script>
</body>
</html>
'''
# ------------------------
# End templates
# ------------------------

# ------------------------
# App config & helpers
# ------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "doc"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB

# Simple SQLite (via sqlite3) for compactness (no SQLAlchemy dependency)
import sqlite3
DB_PATH = os.path.join(BASE_DIR, "phenbot.db")

def get_db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY, user_id INTEGER, subject TEXT, mode TEXT, length_pref TEXT, question TEXT, answer TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_files (id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT, original_filename TEXT, file_path TEXT, file_type TEXT, upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, front TEXT, back TEXT, subject TEXT, difficulty TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(path):
    try:
        text = ""
        with open(path, 'rb') as fh:
            reader = PyPDF2.PdfReader(fh)
            for p in reader.pages:
                t = p.extract_text() or ""
                text += t + "\n"
        return text.strip()
    except Exception as e:
        print("PDF extract error:", e)
        return None

def create_user(username, password):
    try:
        ph = generate_password_hash(password)
        conn = get_db_conn(); c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", (username, ph))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print("create_user error:", e); return False

def get_user(username):
    conn = get_db_conn(); c = conn.cursor()
    c.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone(); conn.close()
    return row

def save_chat_history(user_id, subject, mode, length_pref, question, answer):
    try:
        conn = get_db_conn(); c = conn.cursor()
        c.execute("INSERT INTO chat_history (user_id, subject, mode, length_pref, question, answer) VALUES (?,?,?,?,?,?)", (user_id, subject, mode, length_pref, question, answer))
        conn.commit(); conn.close()
    except Exception as e:
        print("save_chat_history error:", e)

def save_uploaded_file(user_id, filename, original, path, file_type):
    try:
        conn = get_db_conn(); c = conn.cursor()
        c.execute("INSERT INTO uploaded_files (user_id, filename, original_filename, file_path, file_type) VALUES (?,?,?,?,?)", (user_id, filename, original, path, file_type))
        fid = c.lastrowid; conn.commit(); conn.close(); return fid
    except Exception as e:
        print("save_uploaded_file error:", e); return None

def save_flashcard(user_id, title, front, back, subject, difficulty):
    try:
        conn = get_db_conn(); c = conn.cursor()
        c.execute("INSERT INTO flashcards (user_id, title, front, back, subject, difficulty) VALUES (?,?,?,?,?,?)", (user_id, title, front, back, subject, difficulty))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print("save_flashcard error:", e); return False

# AI wrapper: use Groq if available and configured, else OpenAI if configured
def initialize_ai_clients():
    global groq_client, openai
    if GROQ_AVAILABLE and os.environ.get("GROQ_API_KEY"):
        try:
            groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
            print("Groq client initialized")
        except Exception as e:
            print("Groq init failed:", e)
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        print("OpenAI client configured")

initialize_ai_clients()

def ai_get_response(question, subject='general', mode='normal', length='normal', context=None):
    # Build instruction
    subject_prompts = {
        'math': 'You are PhenBOT, a helpful maths tutor.',
        'science': 'You are PhenBOT, a science educator.',
        'english': 'You are PhenBOT, an English tutor.',
        'history': 'You are PhenBOT, a history educator.',
        'general': 'You are PhenBOT, an AI study assistant.'
    }
    mode_instructions = {
        'normal': 'Provide a clear helpful answer.',
        'analogy': 'Explain using analogies.',
        'quiz': 'Generate quiz-style questions and brief answers.',
        'teach': 'Explain step-by-step with examples.',
        'socratic': 'Ask guiding questions to help the user think.',
        'explain': 'Explain like I am five.',
        'summary': 'Provide concise summary and key points.'
    }
    length_instructions = {
        'short': 'Keep it to 2-3 sentences.',
        'normal': 'Keep it to 1-2 paragraphs.',
        'detailed': 'Provide a thorough and detailed explanation with examples.'
    }
    system_prompt = subject_prompts.get(subject,'You are PhenBOT.') + ' ' + mode_instructions.get(mode,'') + ' ' + length_instructions.get(length,'')
    if context:
        system_prompt += " Use the following context: " + (context[:2000] + ("..." if len(context)>2000 else ""))
    # Prefer OpenAI if available
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            # Use ChatCompletion if available
            resp = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL","gpt-4o-mini") if os.environ.get("OPENAI_MODEL") else "gpt-4o-mini",
                messages=[
                    {"role":"system","content":system_prompt},
                    {"role":"user","content":question}
                ],
                temperature=0.3,
                max_tokens=800
            )
            content = resp['choices'][0]['message']['content']
            return content
        except Exception as e:
            print("OpenAI call error:", e)
            return f"AI error: {e}"
    # Fallback to Groq if installed and configured
    if GROQ_AVAILABLE and os.environ.get("GROQ_API_KEY"):
        try:
            resp = groq_client.chat.completions.create(
                model=os.environ.get("GROQ_MODEL","llama-3.1-8b-instant"),
                messages=[{"role":"system","content":system_prompt},{"role":"user","content":question}],
                max_tokens=800
            )
            return resp.choices[0].message.content
        except Exception as e:
            print("Groq call error:", e)
            return f"AI error: {e}"
    # Otherwise return fallback message
    return "AI is not configured (set OPENAI_API_KEY or GROQ_API_KEY)."

def ai_generate_flashcards_from_text(text, subject='general', difficulty='medium', count=5):
    prompt = f"Create {count} concise flashcards from the text. Return JSON array of objects like {{'front':'...', 'back':'...','difficulty':'...'}}. Text: {text[:3000]}..."
    result = ai_get_response(prompt, subject=subject, mode='teach', length='detailed', context=text)
    # attempt to extract JSON array
    m = re.search(r'(\[.*\])', result, re.S)
    try:
        if m:
            arr = json.loads(m.group(1))
        else:
            arr = json.loads(result)
    except Exception:
        # fallback: try parsing a simple FRONT:/BACK: format
        cards = []
        parts = re.split(r'-{3,}|\n\s*\n', result)
        for p in parts:
            f = re.search(r'FRONT:\s*(.+)', p, re.I)
            b = re.search(r'BACK:\s*(.+)', p, re.I)
            if f and b:
                cards.append({'front': f.group(1).strip(), 'back': b.group(1).strip(), 'difficulty':difficulty})
        if cards:
            return cards[:count]
        return []
    # normalize
    normalized = []
    for it in arr[:count]:
        front = it.get('front') or it.get('question') or it.get('q') or ""
        back = it.get('back') or it.get('answer') or it.get('a') or ""
        diff = it.get('difficulty') or difficulty
        normalized.append({'front': front.strip(), 'back': back.strip(), 'difficulty': diff})
    return normalized
# ---------- end Part A ----------
# ---------- Part B of 3 ----------
# Authentication helpers
def is_logged_in():
    return session.get('user_id') is not None

def require_login_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return jsonify({'error':'Authentication required'}), 401
        return f(*args, **kwargs)
    return wrapper

# ------------------------
# Routes: auth & pages
# ------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if not username or not password:
            flash('Please fill all fields','error'); return render_template_string(REGISTER_HTML)
        if len(username) < 3 or len(password) < 6:
            flash('Username min 3, password min 6','error'); return render_template_string(REGISTER_HTML)
        ok = create_user(username, password)
        if not ok:
            flash('Username exists','error'); return render_template_string(REGISTER_HTML)
        # log in new user
        u = get_user(username)
        session['user_id'] = u['id']; session['username'] = u['username']
        flash('Account created','success')
        return redirect(url_for('index'))
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET','POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if not username or not password:
            flash('Please fill all fields','error'); return render_template_string(LOGIN_HTML)
        u = get_user(username)
        if not u or not check_password_hash(u['password_hash'], password):
            flash('Invalid credentials','error'); return render_template_string(LOGIN_HTML)
        session['user_id'] = u['id']; session['username'] = u['username']
        flash('Logged in','success')
        return redirect(url_for('index'))
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out','success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template_string(MAIN_APP_HTML, username=session.get('username','User'))

# ------------------------
# Health
# ------------------------
@app.route('/health')
def health():
    return jsonify({
        'ok': True,
        'ai_openai': bool(os.environ.get('OPENAI_API_KEY')),
        'ai_groq': bool(os.environ.get('GROQ_API_KEY')),
        'timestamp': datetime.utcnow().isoformat()
    })

# ------------------------
# Chat endpoints (support both /api/chat and /api/ask for clients)
# ------------------------
@app.route('/api/chat', methods=['POST'])
@require_login_json
def api_chat():
    try:
        data = request.get_json() or {}
        message = (data.get('message') or data.get('question') or '').strip()
        mode = data.get('mode','normal')
        length = data.get('length','normal')
        subject = data.get('subject','general')
        if not message:
            return jsonify({'error':'No message provided'}), 400
        # If user uploaded file context id provided, optionally load it
        context = None
        if data.get('file_id'):
            conn = get_db_conn(); c = conn.cursor()
            c.execute("SELECT file_path FROM uploaded_files WHERE id=? AND user_id=?", (data.get('file_id'), session['user_id']))
            r = c.fetchone(); conn.close()
            if r:
                context = extract_text_from_pdf(r['file_path'])
        # Call AI
        reply = ai_get_response(message, subject=subject, mode=mode, length=length, context=context)
        # Save chat history
        try:
            save_chat_history(session['user_id'], subject, mode, length, message, reply)
        except Exception as e:
            print("save chat failed:", e)
        return jsonify({'reply': reply})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Server error'}), 500

@app.route('/api/ask', methods=['POST'])
@require_login_json
def api_ask():
    # alias to /api/chat
    return api_chat()

# ------------------------
# File upload + processing
# ------------------------
@app.route('/api/upload', methods=['POST'])
@require_login_json
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error':'No file part'}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error':'No selected file'}), 400
        if not allowed_file(f.filename):
            return jsonify({'error':'File type not allowed'}), 400
        orig = secure_filename(f.filename)
        uid = datetime.utcnow().strftime('%Y%m%d_%H%M%S_') + uuid.uuid4().hex[:8] + '_' + orig
        path = os.path.join(UPLOAD_FOLDER, uid)
        f.save(path)
        ft = orig.rsplit('.',1)[1].lower()
        fid = save_uploaded_file(session['user_id'], uid, orig, path, ft)
        extracted = None
        if ft == 'pdf':
            extracted = extract_text_from_pdf(path)
        return jsonify({'success': True, 'file_id': fid, 'filename': orig, 'text_extracted': bool(extracted), 'text_length': len(extracted) if extracted else 0})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Upload failed: '+str(e)}), 500

@app.route('/api/process_pdf', methods=['POST'])
@require_login_json
def api_process_pdf():
    # support direct form upload (frontend uses this)
    try:
        if 'file' in request.files:
            f = request.files['file']
            # we reuse upload logic but keep ephemeral if needed
            orig = secure_filename(f.filename)
            uid = datetime.utcnow().strftime('%Y%m%d_%H%M%S_') + uuid.uuid4().hex[:8] + '_' + orig
            path = os.path.join(UPLOAD_FOLDER, uid)
            f.save(path)
            extracted = extract_text_from_pdf(path)
            if not extracted:
                return jsonify({'error':'Could not extract PDF text'}), 400
            action = (request.form.get('action') or 'summarize')
            if action == 'summarize':
                prompt = f"Summarize the following document in a structured way (3-sentence overview, bullet key points, why it matters):\n\n{extracted[:4000]}..."
                summary = ai_get_response(prompt, subject='general', mode='summary', length='normal', context=extracted)
                return jsonify({'summary': summary, 'original_length': len(extracted)})
            elif action == 'flashcards':
                # optional params
                num = int(request.form.get('num_cards') or 8)
                difficulty = request.form.get('difficulty') or 'medium'
                cards = ai_generate_flashcards_from_text(extracted, subject='general', difficulty=difficulty, count=num)
                return jsonify({'flashcards': cards, 'count': len(cards)})
            else:
                return jsonify({'error':'Unknown action'}), 400
        else:
            return jsonify({'error':'No file uploaded'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Processing failed: '+str(e)}), 500

# ------------------------
# Summarize existing uploaded file by id
# ------------------------
@app.route('/api/summarize_pdf', methods=['POST'])
@require_login_json
def api_summarize_pdf():
    try:
        data = request.get_json() or {}
        file_id = data.get('file_id')
        if not file_id:
            return jsonify({'error':'file_id required'}), 400
        conn = get_db_conn(); c = conn.cursor()
        c.execute("SELECT file_path FROM uploaded_files WHERE id=? AND user_id=?", (file_id, session['user_id']))
        r = c.fetchone(); conn.close()
        if not r:
            return jsonify({'error':'File not found'}), 404
        extracted = extract_text_from_pdf(r['file_path'])
        if not extracted:
            return jsonify({'error':'No text extracted'}), 400
        prompt = f"Summarize the document:\n\n{extracted[:4000]}..."
        summary = ai_get_response(prompt, subject='general', mode='summary', length='detailed', context=extracted)
        return jsonify({'summary': summary})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Summarization failed'}), 500

# ------------------------
# Generate flashcards (topic or file)
# ------------------------
@app.route('/api/generate_flashcards', methods=['POST'])
@require_login_json
def api_generate_flashcards():
    try:
        data = request.get_json() or {}
        source_type = data.get('source_type','topic')
        subject = data.get('subject','general')
        difficulty = data.get('difficulty','medium')
        count = min(int(data.get('count',5)), 20)
        if source_type == 'file':
            file_id = data.get('file_id'); 
            if not file_id: return jsonify({'error':'file_id required for file source'}),400
            conn = get_db_conn(); c = conn.cursor(); c.execute("SELECT file_path FROM uploaded_files WHERE id=? AND user_id=?", (file_id, session['user_id'])); r = c.fetchone(); conn.close()
            if not r: return jsonify({'error':'File not found'}),404
            text = extract_text_from_pdf(r['file_path'])
            if not text: return jsonify({'error':'Could not extract text'}),400
            cards = ai_generate_flashcards_from_text(text, subject=subject, difficulty=difficulty, count=count)
        else:
            topic = (data.get('topic') or '').strip()
            if not topic:
                return jsonify({'error':'topic required'}), 400
            prompt = f"Generate {count} flashcards (JSON array) about {topic} in {subject} at {difficulty} difficulty. Each item should have question/answer/difficulty keys."
            resp = ai_get_response(prompt, subject=subject, mode='teach', length='normal')
            # try parse JSON
            m = re.search(r'(\[.*\])', resp, re.S)
            try:
                arr = json.loads(m.group(1)) if m else json.loads(resp)
                cards = []
                for it in arr[:count]:
                    q = it.get('question') or it.get('front') or it.get('q') or ''
                    a = it.get('answer') or it.get('back') or it.get('a') or ''
                    diff = it.get('difficulty') or difficulty
                    cards.append({'front': q, 'back': a, 'difficulty': diff})
            except Exception:
                # fallback to plain result parsing
                cards = ai_generate_flashcards_from_text(resp, subject=subject, difficulty=difficulty, count=count)
        # optional save to DB
        if data.get('save_flashcards'):
            title = data.get('title') or f"Flashcards - {datetime.utcnow().strftime('%Y-%m-%d')}"
            for c in cards:
                save_flashcard(session['user_id'], title, c.get('front',''), c.get('back',''), subject, difficulty)
        return jsonify({'flashcards': cards, 'count': len(cards)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Flashcard generation failed'}), 500

# ------------------------
# Save a single flashcard API
# ------------------------
@app.route('/api/save_flashcard', methods=['POST'])
@require_login_json
def api_save_flashcard():
    try:
        data = request.get_json() or {}
        front = (data.get('front') or '').strip(); back = (data.get('back') or '').strip()
        title = data.get('title') or f"Flashcard {datetime.utcnow().isoformat()}"
        subject = data.get('subject','general'); difficulty = data.get('difficulty','medium')
        if not front or not back:
            return jsonify({'error':'front and back required'}), 400
        ok = save_flashcard(session['user_id'], title, front, back, subject, difficulty)
        if ok:
            return jsonify({'success':True})
        else:
            return jsonify({'error':'Save failed'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Save failed'}), 500

# ------------------------
# Retrieve flashcards for user
# ------------------------
@app.route('/api/get_flashcards')
@require_login_json
def api_get_flashcards():
    try:
        conn = get_db_conn(); c = conn.cursor()
        c.execute("SELECT id,title,front,back,subject,difficulty,created_at FROM flashcards WHERE user_id=? ORDER BY created_at DESC LIMIT 200", (session['user_id'],))
        rows = c.fetchall(); conn.close()
        out = [dict(row) for row in rows]
        return jsonify({'flashcards': out})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Load failed'}), 500

# ------------------------
# Chat history retrieval
# ------------------------
@app.route('/api/chat_history')
@require_login_json
def api_chat_history():
    try:
        limit = min(int(request.args.get('limit',20)), 200)
        conn = get_db_conn(); c = conn.cursor()
        c.execute("SELECT question,answer,mode,length_pref,timestamp FROM chat_history WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", (session['user_id'], limit))
        rows = c.fetchall(); conn.close()
        return jsonify({'history': [dict(r) for r in rows]})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Failed to load history'}), 500

# ------------------------
# Download uploaded file by id (owner only)
# ------------------------
@app.route('/files/<int:file_id>')
@require_login_json
def download_file(file_id):
    try:
        conn = get_db_conn(); c = conn.cursor()
        c.execute("SELECT file_path, original_filename FROM uploaded_files WHERE id=? AND user_id=?", (file_id, session['user_id']))
        r = c.fetchone(); conn.close()
        if not r:
            return jsonify({'error':'Not found'}), 404
        return send_file(r['file_path'], as_attachment=True, download_name=r['original_filename'])
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error':'Download failed'}), 500

# ------------------------
# Error handlers
# ------------------------
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error':'Not found'}), 404
    return redirect(url_for('login'))

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error':'Internal error'}), 500
    # don't leak trace in production
    flash('Server error occurred','error')
    return redirect(url_for('login'))
# ---------- end Part B ----------
# ---------- Part C of 3 ----------
if __name__ == "__main__":
    # Ensure DB exists
    init_db()
    # Print helpful startup info
    print("Starting PhenBOT single-file app")
    print("OPENAI_API_KEY present:", bool(os.environ.get("OPENAI_API_KEY")))
    print("GROQ_API_KEY present:", bool(os.environ.get("GROQ_API_KEY")))
    port = int(os.environ.get("PORT", 5000))
    # Debug default False for production; set DEBUG env var if you want
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)

# ------------------------
# requirements.txt (use these packages)
# ------------------------
'''
Flask>=2.2
Werkzeug>=2.2
PyPDF2>=3.0
openai>=0.27.0   # only if using OpenAI
groq>=0.4.0      # only if using Groq SDK (optional)
python-dotenv
'''
# ---------- end Part C ----------
