from flask import Flask, request, jsonify, render_template_string
import os
import sys
import json

# Initialize Flask app
app = Flask(__name__)

# Initialize Groq client
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initialize the Groq client with proper error handling"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    try:
        from groq import Groq
        
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            GROQ_ERROR = "Missing GROQ_API_KEY environment variable"
            print(f"Error: {GROQ_ERROR}", file=sys.stderr)
            return False
        
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("✅ Groq client initialized successfully")
        return True
        
    except ImportError:
        GROQ_ERROR = "Groq library not installed"
        print(f"Error: {GROQ_ERROR}", file=sys.stderr)
        return False
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {str(e)}"
        print(f"Error: {GROQ_ERROR}", file=sys.stderr)
        return False

def ask_study_bot(question, subject=None):
    """Enhanced study bot function with subject-specific prompts"""
    if not groq_client:
        return "Study bot is not available. Please check the API key configuration."

    # Subject-specific system prompts
    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Explain concepts step-by-step with clear examples. Use analogies when helpful and break down complex problems into manageable parts.",
        "science": "You are PhenBOT, a science educator. Explain scientific concepts using real-world analogies and examples. Make complex topics accessible and engaging.",
        "english": "You are PhenBOT, an English and Literature assistant. Help with grammar, writing, literature analysis, and language concepts. Provide clear explanations and examples.",
        "history": "You are PhenBOT, a history educator. Present historical information in engaging narratives with context and connections to modern times.",
        "general": "You are PhenBOT, an advanced AI study companion. Provide clear, educational, and helpful responses to academic questions across all subjects."
    }
    
    system_prompt = system_prompts.get(subject, system_prompts["general"])
    
    try:
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"I encountered an error while processing your question: {str(e)}"

# Initialize Groq on startup
initialize_groq()

# Advanced HTML Template with all features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT - Advanced Study Companion</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --accent-color: #4facfe;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --dark-bg: #1e293b;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--primary-gradient);
            min-height: 100vh;
            color: var(--text-primary);
        }

        .app-container {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--card-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
        }

        .sidebar-header {
            padding: 20px;
            background: var(--secondary-gradient);
            color: white;
        }

        .logo {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .tagline {
            font-size: 14px;
            opacity: 0.9;
        }

        .nav-tabs {
            padding: 20px 0;
        }

        .nav-tab {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
            cursor: pointer;
            background: none;
            border: none;
            width: 100%;
            text-align: left;
        }

        .nav-tab:hover, .nav-tab.active {
            background: rgba(79, 172, 254, 0.1);
            color: var(--accent-color);
            border-left-color: var(--accent-color);
        }

        .nav-tab-icon {
            margin-right: 12px;
            font-size: 18px;
        }

        .streak-section {
            margin-top: auto;
            padding: 20px;
            background: linear-gradient(135deg, #fef3c7, #fbbf24);
            margin: 20px;
            border-radius: 12px;
            text-align: center;
        }

        .streak-counter {
            font-size: 32px;
            font-weight: 700;
            color: #92400e;
        }

        .streak-label {
            font-size: 14px;
            color: #92400e;
            margin-top: 5px;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .top-bar {
            background: var(--card-bg);
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .system-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .system-status.online {
            background: var(--success-color);
            color: white;
        }

        .system-status.offline {
            background: var(--error-color);
            color: white;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .accuracy-meter {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .accuracy-score {
            background: var(--success-color);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .pomodoro-timer {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--warning-color);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
        }

        .content-area {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: rgba(255, 255, 255, 0.05);
        }

        /* Tab Content */
        .tab-content {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Chat Interface */
        .chat-container {
            background: var(--card-bg);
            border-radius: 16px;
            box-shadow: var(--shadow-lg);
            height: 70vh;
            display: flex;
            flex-direction: column;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        .message {
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }

        .message.user {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }

        .message.bot .message-avatar {
            background: var(--secondary-gradient);
            color: white;
        }

        .message.user .message-avatar {
            background: var(--primary-gradient);
            color: white;
        }

        .message-content {
            max-width: 70%;
            padding: 16px 20px;
            border-radius: 18px;
            line-height: 1.6;
            position: relative;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .message.bot .message-content {
            background: #f1f5f9;
            border-bottom-left-radius: 6px;
        }

        .message.user .message-content {
            background: var(--accent-color);
            color: white;
            border-bottom-right-radius: 6px;
        }

        .message-tools {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }

        .tool-btn {
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .tool-btn:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }

        .chat-input-area {
            padding: 20px;
            border-top: 1px solid var(--border-color);
        }

        .input-container {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .message-input {
            flex: 1;
            min-height: 50px;
            max-height: 120px;
            padding: 15px 20px;
            border: 2px solid var(--border-color);
            border-radius: 25px;
            outline: none;
            font-size: 16px;
            resize: none;
            font-family: inherit;
            transition: border-color 0.3s ease;
        }

        .message-input:focus {
            border-color: var(--accent-color);
        }

        .input-tools {
            display: flex;
            gap: 8px;
        }

        .input-tool {
            background: var(--border-color);
            border: none;
            padding: 12px;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .input-tool:hover {
            background: var(--accent-color);
            color: white;
        }

        .send-button {
            background: var(--secondary-gradient);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s ease;
            font-size: 18px;
        }

        .send-button:hover { transform: scale(1.05); }
        .send-button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        /* Dashboard Cards */
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 24px; }
        .dashboard-card { background: var(--card-bg); border-radius: 16px; padding: 24px; box-shadow: var(--shadow); transition: transform 0.3s ease; }
        .dashboard-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
        .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .card-title { font-size: 18px; font-weight: 600; color: var(--text-primary); }
        .card-icon { font-size: 24px; color: var(--accent-color); }

        /* Progress Components */
        .progress-bar { width: 100%; height: 8px; background: var(--border-color); border-radius: 4px; overflow: hidden; margin: 12px 0; }
        .progress-fill { height: 100%; background: var(--secondary-gradient); border-radius: 4px; transition: width 0.3s ease; }

        /* Study Tools */
        .study-tools { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-top: 24px; }
        .study-tool { background: var(--card-bg); border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.3s ease; border: 2px solid transparent; }
        .study-tool:hover { border-color: var(--accent-color); transform: translateY(-2px); }
        .study-tool-icon { font-size: 32px; color: var(--accent-color); margin-bottom: 12px; }

        /* Bookmark Panel */
        .bookmark-item { background: var(--card-bg); border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 4px solid var(--accent-color); }
        .bookmark-title { font-weight: 600; margin-bottom: 8px; }
        .bookmark-preview { font-size: 14px; color: var(--text-secondary); }

        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar { position: absolute; left: -280px; z-index: 1000; height: 100vh; }
            .sidebar.open { transform: translateX(280px); }
            .main-content { width: 100%; }
            .dashboard-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo">🤖 PhenBOT</div>
                <div class="tagline">Advanced Study Companion</div>
            </div>

            <nav class="nav-tabs">
                <button class="nav-tab active" data-tab="dashboard"><span class="nav-tab-icon">📊</span>Dashboard</button>
                <button class="nav-tab" data-tab="math"><span class="nav-tab-icon">🔢</span>Mathematics</button>
                <button class="nav-tab" data-tab="science"><span class="nav-tab-icon">🔬</span>Science</button>
                <button class="nav-tab" data-tab="english"><span class="nav-tab-icon">📚</span>English</button>
                <button class="nav-tab" data-tab="history"><span class="nav-tab-icon">🏛️</span>History</button>
                <button class="nav-tab" data-tab="tools"><span class="nav-tab-icon">🛠️</span>Study Tools</button>
                <button class="nav-tab" data-tab="bookmarks"><span class="nav-tab-icon">📖</span>Bookmarks</button>
                <button class="nav-tab" data-tab="analytics"><span class="nav-tab-icon">📈</span>Analytics</button>
            </nav>

            <div class="streak-section">
                <div class="streak-counter" id="streakCounter">7</div>
                <div class="streak-label">Day Streak 🔥</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="top-bar">
                <button id="sidebarToggle" class="input-tool">☰</button>
                <div class="system-status" id="systemStatus">🔄 Checking...</div>
                <div class="user-info">
                    <div class="accuracy-meter">
                        <span>Accuracy:</span>
                        <span class="accuracy-score" id="accuracyScore">92%</span>
                    </div>
                    <div class="pomodoro-timer" id="pomodoroTimer">🍅 25:00</div>
                </div>
            </div>

            <div class="content-area">
                <!-- Dashboard Tab -->
                <div class="tab-content active" id="dashboard">
                    <div class="dashboard-grid">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Today's Progress</div>
                                <div class="card-icon">📅</div>
                            </div>
                            <div class="progress-bar"><div class="progress-fill" style="width: 65%"></div></div>
                            <p>65% of daily goals completed</p>
                        </div>

                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Recent Activity</div>
                                <div class="card-icon">⚡</div>
                            </div>
                            <ul id="recentActivity">
                                <li>✅ Completed Math Quiz</li>
                                <li>📖 Reviewed Science Notes</li>
                                <li>🎯 Answered 12 Questions</li>
                            </ul>
                        </div>

                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">AI Status</div>
                                <div class="card-icon">🤖</div>
                            </div>
                            <div id="aiStatusDetails">
                                <p id="groqStatus">Checking AI connection...</p>
                                <p id="apiKeyStatus">Verifying API key...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Subject-specific chat tabs -->
                <div class="tab-content" id="math">
                    <div class="chat-container">
                        <div class="chat-messages" id="mathMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    Welcome to Mathematics! I'm here to help you understand concepts through step-by-step explanations and analogies.
                                    <div class="message-tools">
                                        <button class="tool-btn" onclick="bookmarkMessage(this)">📖 Save</button>
                                        <button class="tool-btn" onclick="requestAnalogy(this)">💡 Analogy</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a math question..." data-subject="math"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                </div>
                                <button class="send-button" aria-label="Send message">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="science">
                    <div class="chat-container">
                        <div class="chat-messages" id="scienceMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Ready to explore Science! I can explain complex concepts using real-world analogies.</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a science question..." data-subject="science"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                </div>
                                <button class="send-button" aria-label="Send message">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="english">
                    <div class="chat-container">
                        <div class="chat-messages" id="englishMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Let's dive into English & Literature!</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask about English/Literature..." data-subject="english"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                </div>
                                <button class="send-button" aria-label="Send message">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="history">
                    <div class="chat-container">
                        <div class="chat-messages" id="historyMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Welcome to History! I'll help with stories and timelines.</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a history question..." data-subject="history"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                </div>
                                <button class="send-button" aria-label="Send message">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Tools Tab -->
                <div class="tab-content" id="tools">
                    <h2 style="margin-bottom: 24px;">Study Tools & Resources</h2>
                    <div class="study-tools">
                        <div class="study-tool" onclick="startQuickQuiz()">
                            <div class="study-tool-icon">⚡</div>
                            <h3>Quick Quiz</h3>
                            <p>Test your knowledge</p>
                        </div>
                        <div class="study-tool" onclick="createFlashcards()">
                            <div class="study-tool-icon">🗂️</div>
                            <h3>Flashcards</h3>
                            <p>Review key concepts</p>
                        </div>
                        <div class="study-tool" onclick="generateSummary()">
                            <div class="study-tool-icon">📄</div>
                            <h3>Summary</h3>
                            <p>Quick concept recap</p>
                        </div>
                        <div class="study-tool" onclick="uploadFile()">
                            <div class="study-tool-icon">📁</div>
                            <h3>Upload Notes</h3>
                            <p>Convert to study material</p>
                        </div>
                    </div>
                </div>

                <!-- Bookmarks Tab -->
                <div class="tab-content" id="bookmarks">
                    <h2 style="margin-bottom: 24px;">Saved Answers & Bookmarks</h2>
                    <div id="bookmarksList">
                        <div class="bookmark-item">
                            <div class="bookmark-title">Quadratic Formula Explanation</div>
                            <div class="bookmark-preview">The quadratic formula is used to solve equations of the form ax² + bx + c = 0...</div>
                        </div>
                    </div>
                </div>

                <!-- Analytics Tab -->
                <div class="tab-content" id="analytics">
                    <h2 style="margin-bottom: 24px;">Learning Analytics</h2>
                    <div class="dashboard-grid">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Questions Asked</div>
                                <div class="card-icon">❓</div>
                            </div>
                            <p id="questionCount">47 questions this week</p>
                        </div>
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Study Time</div>
                                <div class="card-icon">⏱️</div>
                            </div>
                            <p id="studyTime">12.5 hours this week</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let isSystemReady = false;
        let bookmarks = JSON.parse(localStorage.getItem('phenbot_bookmarks') || '[]');
        let analytics = JSON.parse(localStorage.getItem('phenbot_analytics') || '{"questionsAsked": 0, "studyTime": 0}');

        // Initialize app
        document.addEventListener('DOMContentLoaded', () => {
            setupTabs();
            setupSidebar();
            setupChats();
            checkSystemStatus();
            updateAnalytics();
        });

        // Tab system
        function setupTabs() {
            const tabs = document.querySelectorAll('.nav-tab');
            const tabContents = document.querySelectorAll('.tab-content');

            function activateTab(targetId) {
                tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === targetId));
                tabContents.forEach(c => c.classList.toggle('active', c.id === targetId));
            }

            tabs.forEach(tab => {
                tab.addEventListener('click', () => activateTab(tab.dataset.tab));
            });
        }

        // Sidebar toggle for mobile
        function setupSidebar() {
            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.getElementById('sidebarToggle');
            
            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', () => {
                    sidebar.classList.toggle('open');
                });
            }
        }

        // Chat system
        function setupChats() {
            document.querySelectorAll('.chat-container').forEach(container => {
                const textarea = container.querySelector('.message-input');
                const sendBtn = container.querySelector('.send-button');
                const messagesEl = container.querySelector('.chat-messages');
                
                if (!textarea || !sendBtn || !messagesEl) return;

                function updateSendButton() {
                    sendBtn.disabled = !textarea.value.trim() || !isSystemReady;
                }

                textarea.addEventListener('input', updateSendButton);
                textarea.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (!sendBtn.disabled) sendMessage();
                    }
                });

                sendBtn.addEventListener('click', sendMessage);

                async function sendMessage() {
                    const question = textarea.value.trim();
                    if (!question || !isSystemReady) return;

                    const subject = textarea.dataset.subject || 'general';
                    
                    // Add user message
                    appendMessage(messagesEl, 'user', question);
                    
                    // Clear input
                    textarea.value = '';
                    updateSendButton();

                    // Add thinking message
                    const thinkingMsg = appendMessage(messagesEl, 'bot', '🤔 Thinking...');
                    
                    // Update analytics
                    analytics.questionsAsked++;
                    saveAnalytics();
                    updateAnalytics();

                    try {
                        const response = await fetch('/api/ask', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ 
                                question: question,
                                subject: subject
                            })
                        });

                        const data = await response.json();
                        
                        // Remove thinking message
                        thinkingMsg.remove();

                        if (response.ok) {
                            const botMsg = appendMessage(messagesEl, 'bot', data.answer || 'No response received');
                            addMessageTools(botMsg);
                        } else {
                            appendMessage(messagesEl, 'bot', `Error: ${data.error || 'Unknown error'}`);
                        }

                    } catch (error) {
                        thinkingMsg.remove();
                        appendMessage(messagesEl, 'bot', `Network error: ${error.message}`);
                    }

                    textarea.focus();
                }

                function appendMessage(container, type, content) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${type}`;
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = type === 'user' ? 'You' : '🤖';
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = content;
                    
                    messageDiv.appendChild(avatar);
                    messageDiv.appendChild(messageContent);
                    container.appendChild(messageDiv);
                    container.scrollTop = container.scrollHeight;
                    
                    return messageDiv;
                }

                function addMessageTools(messageDiv) {
                    if (messageDiv.classList.contains('bot')) {
                        const content = messageDiv.querySelector('.message-content');
                        const tools = document.createElement('div');
                        tools.className = 'message-tools';
                        tools.innerHTML = `
                            <button class="tool-btn" onclick="bookmarkMessage(this)">📖 Save</button>
                            <button class="tool-btn" onclick="copyMessage(this)">📋 Copy</button>
                            <button class="tool-btn" onclick="shareMessage(this)">🔗 Share</button>
                        `;
                        content.appendChild(tools);
                    }
                }

                updateSendButton();
            });
        }

        // System status check
        async function checkSystemStatus() {
            const statusEl = document.getElementById('systemStatus');
            const groqStatusEl = document.getElementById('groqStatus');
            const apiKeyStatusEl = document.getElementById('apiKeyStatus');
            
            try {
                statusEl.textContent = '🔄 Checking...';
                statusEl.className = 'system-status';
                
                const response = await fetch('/health');
                const data = await response.json();
                
                if (data.groq_available && data.api_key_present) {
                    statusEl.textContent = '🟢 AI Online';
                    statusEl.className = 'system-status online';
                    isSystemReady = true;
                    
                    if (groqStatusEl) groqStatusEl.textContent = '✅ Groq AI connected';
                    if (apiKeyStatusEl) apiKeyStatusEl.textContent = '✅ API key valid';
                    
                } else {
                    statusEl.textContent = '🔴 AI Offline';
                    statusEl.className = 'system-status offline';
                    
                    if (groqStatusEl) groqStatusEl.textContent = data.groq_available ? '✅ Groq available' : '❌ Groq unavailable';
                    if (apiKeyStatusEl) apiKeyStatusEl.textContent = data.api_key_present ? '✅ API key found' : '❌ API key missing';
                }
                
                // Update all send buttons
                document.querySelectorAll('.send-button').forEach(btn => {
                    btn.disabled = !isSystemReady;
                });
                
            } catch (error) {
                statusEl.textContent = '🔴 Connection Failed';
                statusEl.className = 'system-status offline';
                console.error('Status check failed:', error);
            }
        }

        // Analytics functions
        function updateAnalytics() {
            const questionCountEl = document.getElementById('questionCount');
            const studyTimeEl = document.getElementById('studyTime');
            
            if (questionCountEl) questionCountEl.textContent = `${analytics.questionsAsked} questions this week`;
            if (studyTimeEl) studyTimeEl.textContent = `${analytics.studyTime} hours this week`;
        }

        function saveAnalytics() {
            localStorage.setItem('phenbot_analytics', JSON.stringify(analytics));
        }

        // Tool functions
        function bookmarkMessage(btn) {
            const messageContent = btn.closest('.message-content');
            const text = messageContent.textContent.replace(/📖 Save📋 Copy🔗 Share/, '').trim();
            
            const bookmark = {
                id: Date.now(),
                title: text.split('\n')[0].substring(0, 50) + '...',
                content: text,
                timestamp: new Date().toISOString()
            };
            
            bookmarks.unshift(bookmark);
            localStorage.setItem('phenbot_bookmarks', JSON.stringify(bookmarks));
            
            btn.textContent = '📖 Saved';
            btn.disabled = true;
            
            updateBookmarksList();
        }

        function copyMessage(btn) {
            const messageContent = btn.closest('.message-content');
            const text = messageContent.textContent.replace(/📖 Save📋 Copy🔗 Share/, '').trim();
            
            navigator.clipboard.writeText(text).then(() => {
                btn.textContent = '📋 Copied';
                setTimeout(() => {
                    btn.textContent = '📋 Copy';
                }, 2000);
            });
        }

        function shareMessage(btn) {
            const messageContent = btn.closest('.message-content');
            const text = messageContent.textContent.replace(/📖 Save📋 Copy🔗 Share/, '').trim();
            
            if (navigator.share) {
                navigator.share({
                    title: 'PhenBOT Answer',
                    text: text
                });
            } else {
                copyMessage(btn);
            }
        }

        function updateBookmarksList() {
            const bookmarksList = document.getElementById('bookmarksList');
            if (!bookmarksList) return;
            
            bookmarksList.innerHTML = bookmarks.map(bookmark => `
                <div class="bookmark-item">
                    <div class="bookmark-title">${bookmark.title}</div>
                    <div class="bookmark-preview">${bookmark.content.substring(0, 200)}...</div>
                    <small style="color: var(--text-secondary);">${new Date(bookmark.timestamp).toLocaleDateString()}</small>
                </div>
            `).join('');
        }

        // Study tool functions
        function startQuickQuiz() {
            if (!isSystemReady) {
                alert('AI system not ready. Please wait for connection.');
                return;
            }
            alert('Quick Quiz feature coming soon! This will generate personalized quizzes based on your study history.');
        }

        function createFlashcards() {
            if (!isSystemReady) {
                alert('AI system not ready. Please wait for connection.');
                return;
            }
            alert('Flashcard generator coming soon! Upload your notes and I\'ll create flashcards automatically.');
        }

        function generateSummary() {
            if (!isSystemReady) {
                alert('AI system not ready. Please wait for connection.');
                return;
            }
            alert('Summary generator coming soon! I\'ll create concise summaries of any topic you need.');
        }

        function uploadFile() {
            alert('File upload feature coming soon! You\'ll be able to upload PDFs, images, and documents for analysis.');
        }

        function voiceInput() {
            alert('Voice input feature coming soon! Ask questions by speaking instead of typing.');
        }

        function requestAnalogy(btn) {
            const messageContent = btn.closest('.message-content');
            const text = messageContent.textContent.replace(/📖 Save💡 Analogy/, '').trim();
            
            // Find the chat container and simulate a new question
            const chatContainer = btn.closest('.chat-container');
            const textarea = chatContainer.querySelector('.message-input');
            
            textarea.value = `Can you explain "${text}" using a simple real-world analogy?`;
            chatContainer.querySelector('.send-button').click();
        }

        // Initialize bookmarks on load
        setTimeout(() => {
            updateBookmarksList();
        }, 100);

        // Pomodoro timer (simple version)
        function startPomodoroTimer() {
            let minutes = 25;
            let seconds = 0;
            const timerEl = document.getElementById('pomodoroTimer');
            
            const interval = setInterval(() => {
                seconds--;
                if (seconds < 0) {
                    minutes--;
                    seconds = 59;
                }
                
                if (minutes < 0) {
                    clearInterval(interval);
                    timerEl.textContent = '🍅 Break Time!';
                    alert('Pomodoro session complete! Time for a break.');
                    return;
                }
                
                timerEl.textContent = `🍅 ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);
        }

        // Auto-start timer on click
        document.getElementById('pomodoroTimer').addEventListener('click', startPomodoroTimer);

        // Update streak counter occasionally
        setInterval(() => {
            const streak = Math.floor(Math.random() * 3) + 7; // 7-9 days
            document.getElementById('streakCounter').textContent = streak;
        }, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main application"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'status': 'healthy'
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """Enhanced API endpoint with subject support"""
    try:
        if not GROQ_AVAILABLE:
            return jsonify({
                'error': f'AI system not available: {GROQ_ERROR}'
            }), 500
        
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question'].strip()
        subject = data.get('subject', 'general')
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Get answer from enhanced study bot
        answer = ask_study_bot(question, subject)
        
        return jsonify({
            'answer': answer,
            'sources': [],  # For future enhancement
            'subject': subject
        })
        
    except Exception as e:
        print(f"Error in api_ask: {str(e)}", file=sys.stderr)
        return jsonify({
            'error': f'Failed to process question: {str(e)}'
        }), 500

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'PhenBOT is running!',
        'groq_status': GROQ_AVAILABLE,
        'environment': 'Railway'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 Starting PhenBOT on port {port}")
    print(f"🤖 Groq available: {GROQ_AVAILABLE}")
    if GROQ_ERROR:
        print(f"❌ Groq error: {GROQ_ERROR}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
