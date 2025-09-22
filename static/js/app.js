// static/js/app.js
(() => {
  // DOM refs
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const chatMode = document.getElementById("chatMode");
  const responseLength = document.getElementById("responseLength");
  const voiceBtn = document.getElementById("voiceBtn");

  // PDF UI
  const uploadArea = document.getElementById("uploadArea");
  const pdfInput = document.getElementById("pdfInput");
  const summarizeBtn = document.getElementById("summarizeBtn");
  const flashcardBtn = document.getElementById("flashcardBtn");
  const pdfResult = document.getElementById("pdfResult");
  const numCards = document.getElementById("numCards");
  const cardDifficulty = document.getElementById("cardDifficulty");

  // Flashcards UI
  const flashcardsList = document.getElementById("flashcardsList");
  const addFlashcardBtn = document.getElementById("addFlashcardBtn");
  const newQuestion = document.getElementById("newQuestion");
  const newAnswer = document.getElementById("newAnswer");

  // Pomodoro
  const startTimerBtn = document.getElementById("startTimerBtn");
  const pauseTimerBtn = document.getElementById("pauseTimerBtn");
  const resetTimerBtn = document.getElementById("resetTimerBtn");
  const focusMinutes = document.getElementById("focusMinutes");
  const breakMinutes = document.getElementById("breakMinutes");
  const timerDisplay = document.getElementById("timerDisplay");
  const miniTimer = document.getElementById("miniTimer");

  // State
  let isRecording = false;
  let recognition = null;
  let synth = window.speechSynthesis;
  let pomodoroInterval = null;
  let remainingSeconds = parseInt(focusMinutes.value) * 60;
  let inBreak = false;

  // Helpers: UI message blocks
  function appendMessage({ role, text }) {
    const msg = document.createElement("div");
    msg.className = "message " + (role === "user" ? "user" : "bot");
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.style.background = role === "user"
      ? "linear-gradient(135deg,#4f46e5,#7c3aed)"
      : "linear-gradient(135deg,#10b981,#06b6d4)";
    avatar.innerHTML = role === "user" ? "You" : "<i class='fas fa-robot'></i>";

    const content = document.createElement("div");
    content.className = "message-content";
    content.innerHTML = text.replace(/\n/g, "<br>");

    msg.appendChild(avatar);
    msg.appendChild(content);
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showTypingIndicator() {
    const t = document.createElement("div");
    t.className = "message bot typing";
    t.id = "typingInd";
    t.innerHTML = `<div class="message-avatar" style="background:linear-gradient(135deg,#10b981,#06b6d4)"><i class="fas fa-robot"></i></div>
      <div class="message-content typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
    chatMessages.appendChild(t);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function removeTypingIndicator() {
    const t = document.getElementById("typingInd");
    if (t) t.remove();
  }

  // Chat send
  async function sendChat() {
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage({ role: "user", text });
    chatInput.value = "";
    showTypingIndicator();

    const payload = {
      message: text,
      mode: chatMode.value,
      length: responseLength.value
    };

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      removeTypingIndicator();
      if (data.error) {
        appendMessage({ role: "bot", text: "Error: " + data.error });
      } else {
        appendMessage({ role: "bot", text: data.reply });
        speakText(data.reply);
      }
    } catch (err) {
      removeTypingIndicator();
      appendMessage({ role: "bot", text: "Network error: " + err.message });
    }
  }

  // keyboard: Enter to send, Shift+Enter newline
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  });

  sendBtn.addEventListener("click", sendChat);

  // voice: Web Speech API
  function initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      voiceBtn.style.display = "none";
      return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.onresult = (ev) => {
      const sentence = Array.from(ev.results).map(r => r[0].transcript).join("");
      chatInput.value = sentence;
      sendChat();
    };
    recognition.onend = () => {
      isRecording = false;
      voiceBtn.style.background = "";
    };
    recognition.onerror = (e) => {
      console.error("Speech error", e);
      isRecording = false;
      voiceBtn.style.background = "";
    };
  }

  voiceBtn?.addEventListener("click", () => {
    if (!recognition) return;
    if (!isRecording) {
      recognition.start();
      isRecording = true;
      voiceBtn.style.background = "var(--primary-red)";
    } else {
      recognition.stop();
      isRecording = false;
      voiceBtn.style.background = "";
    }
  });

  function speakText(text) {
    if (!("speechSynthesis" in window)) return;
    const utter = new SpeechSynthesisUtterance();
    utter.text = text;
    utter.rate = 1;
    utter.pitch = 1;
    utter.lang = "en-US";
    // pick a voice if available
    const voices = synth.getVoices();
    if (voices.length) utter.voice = voices[0];
    synth.speak(utter);
  }

  // PDF upload & actions
  uploadArea.addEventListener("click", () => pdfInput.click());
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("dragover");
  });
  uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      pdfInput.files = e.dataTransfer.files;
    }
  });

  pdfInput.addEventListener("change", () => {
    const f = pdfInput.files[0];
    if (f) {
      uploadArea.innerHTML = `<div style="font-size:1rem;color:var(--text-primary)"><i class="fas fa-file-pdf"></i> ${f.name}</div><div style="font-size:0.85rem;color:var(--text-muted)">Ready</div>`;
    }
  });

  async function processPdf(action) {
    const f = pdfInput.files[0];
    if (!f) {
      pdfResult.innerText = "Please upload a PDF first.";
      return;
    }
    pdfResult.innerText = "Working... (this can take up to 20s)";
    const form = new FormData();
    form.append("file", f);
    form.append("action", action);
    if (action === "flashcards") {
      form.append("num_cards", numCards.value || 8);
      form.append("difficulty", cardDifficulty.value || "medium");
    }
    try {
      const res = await fetch("/api/process_pdf", { method: "POST", body: form });
      const data = await res.json();
      if (data.error) {
        pdfResult.innerText = "Error: " + data.error;
        return;
      }
      if (action === "summarize") {
        pdfResult.innerText = data.summary || JSON.stringify(data);
      } else if (action === "flashcards") {
        // prefer parsed flashcards
        if (data.flashcards) {
          const cards = data.flashcards;
          pdfResult.innerText = `Generated ${cards.length} flashcards. Added to your Flashcards list.`;
          addFlashcardsToUI(cards);
        } else {
          pdfResult.innerText = data.raw || "No flashcards returned.";
        }
      }
    } catch (err) {
      pdfResult.innerText = "Network error: " + err.message;
    }
  }

  summarizeBtn.addEventListener("click", () => processPdf("summarize"));
  flashcardBtn.addEventListener("click", () => processPdf("flashcards"));

  // Flashcards: add manual or AI generated
  function addFlashcardUI(question, answer, difficulty = "medium") {
    const wrapper = document.createElement("div");
    wrapper.className = "flashcard";
    wrapper.innerHTML = `
      <div class="card-inner">
        <div class="card-front" style="font-weight:700;">${escapeHtml(question)}</div>
        <div class="card-back" style="display:none;margin-top:8px;color:var(--text-muted)">${escapeHtml(answer)}</div>
      </div>
    `;
    // toggle
    wrapper.addEventListener("click", () => {
      const front = wrapper.querySelector(".card-front");
      const back = wrapper.querySelector(".card-back");
      if (back.style.display === "none") {
        front.style.display = "none";
        back.style.display = "block";
      } else {
        back.style.display = "none";
        front.style.display = "block";
      }
    });
    flashcardsList.prepend(wrapper);
  }

  function addFlashcardsToUI(cards) {
    try {
      cards.forEach(c => {
        addFlashcardUI(c.question || c.q || "Q?", c.answer || c.a || c.answer_text || "A");
      });
    } catch (e) {
      console.error("Failed to add cards", e);
    }
  }

  addFlashcardBtn.addEventListener("click", () => {
    const q = newQuestion.value.trim();
    const a = newAnswer.value.trim();
    if (!q || !a) return;
    addFlashcardUI(q, a);
    newQuestion.value = "";
    newAnswer.value = "";
  });

  // Pomodoro functions
  function formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
  }

  function updateTimerDisplays() {
    timerDisplay.innerText = formatTime(remainingSeconds);
    miniTimer.innerText = formatTime(remainingSeconds);
  }

  function startPomodoro() {
    if (pomodoroInterval) return;
    pomodoroInterval = setInterval(() => {
      if (remainingSeconds <= 0) {
        // switch
        inBreak = !inBreak;
        if (inBreak) {
          remainingSeconds = (parseInt(breakMinutes.value) || 5) * 60;
          speakText("Break time! Relax for a few minutes.");
        } else {
          remainingSeconds = (parseInt(focusMinutes.value) || 25) * 60;
          speakText("Focus time! Let's get back to studying.");
        }
      } else {
        remainingSeconds -= 1;
      }
      updateTimerDisplays();
    }, 1000);
  }

  function pausePomodoro() {
    if (pomodoroInterval) {
      clearInterval(pomodoroInterval);
      pomodoroInterval = null;
    }
  }

  function resetPomodoro() {
    pausePomodoro();
    inBreak = false;
    remainingSeconds = (parseInt(focusMinutes.value) || 25) * 60;
    updateTimerDisplays();
  }

  startTimerBtn.addEventListener("click", startPomodoro);
  pauseTimerBtn.addEventListener("click", pausePomodoro);
  resetTimerBtn.addEventListener("click", resetPomodoro);

  // small helpers
  function escapeHtml(unsafe) {
    return unsafe
      .replaceAll("&","&amp;")
      .replaceAll("<","&lt;")
      .replaceAll(">","&gt;")
      .replaceAll('"',"&quot;");
  }

  // init
  function init() {
    initSpeech();
    remainingSeconds = (parseInt(focusMinutes.value) || 25) * 60;
    updateTimerDisplays();

    // page nav (basic)
    document.querySelectorAll(".nav-item").forEach(n => {
      n.addEventListener("click", () => {
        document.querySelectorAll(".nav-item").forEach(x => x.classList.remove("active"));
        n.classList.add("active");
        const tab = n.dataset.tab;
        document.getElementById("pageTitle").innerText = n.innerText.trim();
      });
    });
  }

  window.addEventListener("load", init);
})();
