from flask import Flask, request, jsonify, render_template_string
import os
import sys
import json

app = Flask(__name__)

# Initialize Groq client
groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
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
    if not groq_client:
        return "Study bot is not available. Please check the API key configuration."

    system_prompts = {
        "math": "You are PhenBOT, a mathematics tutor. Explain concepts step-by-step with clear examples.",
        "science": "You are PhenBOT, a science educator. Explain concepts using real-world analogies.",
        "english": "You are PhenBOT, an English tutor. Help with grammar, writing, and literature.",
        "history": "You are PhenBOT, a history educator. Present information in engaging narratives.",
        "general": "You are PhenBOT, an AI study companion. Provide clear, helpful responses."
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
        return f"Error processing question: {str(e)}"

initialize_groq()

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
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--primary-gradient);
            min-height: 100vh;
            color: var(--text-primary);
        }

        .app-container {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

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
            flex: 1;
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
            font-size: 14px;
        }

        .nav-tab:hover, .nav-tab.active {
            background: rgba(79, 172, 254, 0.1);
            color: var(--accent-color);
            border-left-color: var(--accent-color);
        }

        .nav-tab-icon {
            margin-right: 12px;
            font-size: 16px;
            width: 20px;
            text-align: center;
        }

        .streak-section {
            margin: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #fef3c7, #fbbf24);
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
            cursor: pointer;
        }

        .system-status.online {
            background: var(--success-color);
            color: white;
        }

        .system-status.offline {
            background: var(--error-color);
            color: white;
        }

        .system-status.checking {
            background: var(--warning-color);
            color: white;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .accuracy-meter, .pomodoro-timer {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
        }

        .accuracy-meter {
            background: var(--success-color);
            color: white;
        }

        .pomodoro-timer {
            background: var(--warning-color);
            color: white;
        }

        .content-area {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: rgba(255, 255, 255, 0.05);
        }

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
            font-size: 16px;
            flex-shrink: 0;
            font-weight: 600;
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
            font-size: 11px;
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

        .send-button:hover:not(:disabled) { transform: scale(1.05); }
        .send-button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        .dashboard-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 24px; 
            margin-bottom: 24px; 
        }

        .dashboard-card { 
            background: var(--card-bg); 
            border-radius: 16px; 
            padding: 24px; 
            box-shadow: var(--shadow); 
            transition: transform 0.3s ease; 
        }

        .dashboard-card:hover { 
            transform: translateY(-4px); 
            box-shadow: var(--shadow-lg); 
        }

        .card-header { 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
            margin-bottom: 16px; 
        }

        .card-title { 
            font-size: 18px; 
            font-weight: 600; 
            color: var(--text-primary); 
        }

        .card-icon { 
            font-size: 24px; 
            color: var(--accent-color); 
        }

        .progress-bar { 
            width: 100%; 
            height: 8px; 
            background: var(--border-color); 
            border-radius: 4px; 
            overflow: hidden; 
            margin: 12px 0; 
        }

        .progress-fill { 
            height: 100%; 
            background: var(--secondary-gradient); 
            border-radius: 4px; 
            transition: width 0.3s ease; 
        }

        .study-tools { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 16px; 
            margin-top: 24px; 
        }

        .study-tool { 
            background: var(--card-bg); 
            border-radius: 12px; 
            padding: 20px; 
            text-align: center; 
            cursor: pointer; 
            transition: all 0.3s ease; 
            border: 2px solid transparent; 
        }

        .study-tool:hover { 
            border-color: var(--accent-color); 
            transform: translateY(-2px); 
        }

        .study-tool-icon { 
            font-size: 32px; 
            color: var(--accent-color); 
            margin-bottom: 12px; 
        }

        .bookmark-item { 
            background: var(--card-bg); 
            border-radius: 8px; 
            padding: 16px; 
            margin-bottom: 12px; 
            border-left: 4px solid var(--accent-color); 
        }

        .bookmark-title { 
            font-weight: 600; 
            margin-bottom: 8px; 
        }

        .bookmark-preview { 
            font-size: 14px; 
            color: var(--text-secondary); 
        }

        /* Mobile responsive */
        @media (max-width: 768px) {
            .app-container {
                flex-direction: column;
            }
            .sidebar { 
                position: fixed;
                left: -280px; 
                z-index: 1000; 
                height: 100vh;
                width: 280px;
            }
            .sidebar.open { 
                transform: translateX(280px); 
            }
            .main-content { 
                width: 100%; 
            }
            .dashboard-grid { 
                grid-template-columns: 1fr; 
            }
        }

        .sidebar-toggle {
            display: none;
            background: var(--border-color);
            border: none;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        @media (max-width: 768px) {
            .sidebar-toggle {
                display: block;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo">🤖 PhenBOT</div>
                <div class="tagline">Advanced Study Companion</div>
            </div>

            <nav class="nav-tabs">
                <button class="nav-tab active" data-tab="dashboard" type="button">
                    <span class="nav-tab-icon">📊</span>Dashboard
                </button>
                <button class="nav-tab" data-tab="math" type="button">
                    <span class="nav-tab-icon">🔢</span>Mathematics
                </button>
                <button class="nav-tab" data-tab="science" type="button">
                    <span class="nav-tab-icon">🔬</span>Science
                </button>
                <button class="nav-tab" data-tab="english" type="button">
                    <span class="nav-tab-icon">📚</span>English
                </button>
                <button class="nav-tab" data-tab="history" type="button">
                    <span class="nav-tab-icon">🏛️</span>History
                </button>
                <button class="nav-tab" data-tab="tools" type="button">
                    <span class="nav-tab-icon">🛠️</span>Study Tools
                </button>
                <button class="nav-tab" data-tab="bookmarks" type="button">
                    <span class="nav-tab-icon">📖</span>Bookmarks
                </button>
                <button class="nav-tab" data-tab="analytics" type="button">
                    <span class="nav-tab-icon">📈</span>Analytics
                </button>
            </nav>

            <div class="streak-section">
                <div class="streak-counter" id="streakCounter">7</div>
                <div class="streak-label">Day Streak 🔥</div>
            </div>
        </div>

        <div class="main-content">
            <div class="top-bar">
                <button id="sidebarToggle" class="sidebar-toggle" type="button">☰</button>
                <div class="system-status checking" id="systemStatus">🔄 Checking...</div>
                <div class="user-info">
                    <div class="accuracy-meter">
                        <span>Accuracy: 92%</span>
                    </div>
                    <div class="pomodoro-timer" id="pomodoroTimer">🍅 25:00</div>
                </div>
            </div>

            <div class="content-area">
                <div class="tab-content active" id="dashboard">
                    <div class="dashboard-grid">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Today's Progress</div>
                                <div class="card-icon">📅</div>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 65%"></div>
                            </div>
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

                <!-- Math Tab -->
                <div class="tab-content" id="math">
                    <div class="chat-container">
                        <div class="chat-messages" id="mathMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Welcome to Mathematics! I'm here to help you understand concepts through step-by-step explanations and analogies. Ask me anything about math!</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a math question..." data-subject="math"></textarea>
                                <button class="send-button" type="button">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Science Tab -->
                <div class="tab-content" id="science">
                    <div class="chat-container">
                        <div class="chat-messages" id="scienceMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Ready to explore Science! I can explain complex concepts using real-world analogies. What would you like to learn about?</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a science question..." data-subject="science"></textarea>
                                <button class="send-button" type="button">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- English Tab -->
                <div class="tab-content" id="english">
                    <div class="chat-container">
                        <div class="chat-messages" id="englishMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Let's dive into English & Literature! I can help with grammar, writing, analysis, and more.</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask about English/Literature..." data-subject="english"></textarea>
                                <button class="send-button" type="button">➤</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- History Tab -->
                <div class="tab-content" id="history">
                    <div class="chat-container">
                        <div class="chat-messages" id="historyMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">Welcome to History! I'll help you explore the past with engaging stories and clear explanations.</div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a history question..." data-subject="history"></textarea>
                                <button class="send-button" type="button">➤</button>
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
                        <div class="study-tool" onclick="uploadNotes()">
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
                            <div class="bookmark-title">Sample Bookmark</div>
                            <div class="bookmark-preview">Your saved responses will appear here...</div>
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
                            <p id="questionCount">0 questions this week</p>
                        </div>
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Study Time</div>
                                <div class="card-icon">⏱️</div>
                            </div>
                            <p id="studyTime">0 hours this week</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let isSystemReady = false;
        let questionCount = 0;

        // Wait for DOM to be fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing...');
            
            // Initialize all components
            initializeTabs();
            initializeSidebar();
            initializeChats();
            checkSystemStatus();
        });

        function initializeTabs() {
            console.log('Initializing tabs...');
            const tabs = document.querySelectorAll('.nav-tab');
            const tabContents = document.querySelectorAll('.tab-content');

            tabs.forEach(tab => {
                tab.addEventListener('click', function(e) {
                    e.preventDefault();
                    const targetTab = this.dataset.tab;
                    console.log('Switching to tab:', targetTab);
                    
                    // Remove active class from all tabs and contents
                    tabs.forEach(t => t.classList.remove('active'));
                    tabContents.forEach(c => c.classList.remove('active'));
                    
                    // Add active class to clicked tab and corresponding content
                    this.classList.add('active');
                    const targetContent = document.getElementById(targetTab);
                    if (targetContent) {
                        targetContent.classList.add('active');
                    }
                });
            });
        }

        function initializeSidebar() {
            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.getElementById('sidebarToggle');
            
            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', function() {
                    sidebar.classList.toggle('open');
                });
            }
        }

        function initializeChats() {
            console.log('Initializing chats...');
            const chatContainers = document.querySelectorAll('.chat-container');
            
            chatContainers.forEach(container => {
                const textarea = container.querySelector('.message-input');
                const sendBtn = container.querySelector('.send-button');
                const messagesEl = container.querySelector('.chat-messages');
                
                if (!textarea || !sendBtn || !messagesEl) return;

                console.log('Setting up chat for container:', container.closest('.tab-content')?.id);

                function updateSendButton() {
                    const hasText = textarea.value.trim().length > 0;
                    sendBtn.disabled = !hasText || !isSystemReady;
                }

                // Event listeners
                textarea.addEventListener('input', updateSendButton);
                
                textarea.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (!sendBtn.disabled) {
                            sendMessage();
                        }
                    }
                });

                sendBtn.addEventListener('click', sendMessage);

                async function sendMessage() {
                    const question = textarea.value.trim();
                    if (!question || !isSystemReady) return;

                    console.log('Sending message:', question);
                    const subject = textarea.dataset.subject || 'general';
                    
                    // Add user message
                    appendMessage(messagesEl, 'user', question);
                    
                    // Clear input and update button
                    textarea.value = '';
                    updateSendButton();

                    // Add thinking message
                    const thinkingMsg = appendMessage(messagesEl, 'bot', '🤔 Thinking...');
                    
                    // Update question count
                    questionCount++;
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
                        if (thinkingMsg && thinkingMsg.parentNode) {
                            thinkingMsg.parentNode.removeChild(thinkingMsg);
                        }

                        if (response.ok && data.answer) {
                            const botMsg = appendMessage(messagesEl, 'bot', data.answer);
                            addMessageTools(botMsg);
                        } else {
                            appendMessage(messagesEl, 'bot', `Error: ${data.error || 'No response received'}`);
                        }

                    } catch (error) {
                        console.error('Error sending message:', error);
                        if (thinkingMsg && thinkingMsg.parentNode) {
                            thinkingMsg.parentNode.removeChild(thinkingMsg);
                        }
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
                            <button class="tool-btn" onclick="bookmarkMessage(this)" type="button">📖 Save</button>
                            <button class="tool-btn" onclick="copyMessage(this)" type="button">📋 Copy</button>
                        `;
                        content.appendChild(tools);
                    }
                }

                updateSendButton();
            });
        }

        async function checkSystemStatus() {
            console.log('Checking system status...');
            const statusEl = document.getElementById('systemStatus');
            const groqStatusEl = document.getElementById('groqStatus');
            const apiKeyStatusEl = document.getElementById('apiKeyStatus');
            
            try {
                statusEl.textContent = '🔄 Checking...';
                statusEl.className = 'system-status checking';
                
                const response = await fetch('/health');
                const data = await response.json();
                
                console.log('Health check response:', data);
                
                if (data.groq_available && data.api_key_present) {
                    statusEl.textContent = '🟢 AI Online';
                    statusEl.className = 'system-status online';
                    isSystemReady = true;
                    
                    if (groqStatusEl) groqStatusEl.textContent = '✅ Groq AI connected';
                    if (apiKeyStatusEl) apiKeyStatusEl.textContent = '✅ API key valid';
                    
                } else {
                    statusEl.textContent = '🔴 AI Offline';
                    statusEl.className = 'system-status offline';
                    isSystemReady = false;
                    
                    if (groqStatusEl) {
                        groqStatusEl.textContent = data.groq_available ? '✅ Groq available' : '❌ Groq unavailable';
                    }
                    if (apiKeyStatusEl) {
                        apiKeyStatusEl.textContent = data.api_key_present ? '✅ API key found' : '❌ API key missing';
                    }
                }
                
                // Update all send buttons based on system status
                document.querySelectorAll('.send-button').forEach(btn => {
                    btn.disabled = !isSystemReady;
                });
                
                // Update all textareas
                document.querySelectorAll('.message-input').forEach(textarea => {
                    const container = textarea.closest('.chat-container');
                    const sendBtn = container?.querySelector('.send-button');
                    if (sendBtn) {
                        sendBtn.disabled = !textarea.value.trim() || !isSystemReady;
                    }
                });
                
            } catch (error) {
                console.error('Status check failed:', error);
                statusEl.textContent = '🔴 Connection Failed';
                statusEl.className = 'system-status offline';
                isSystemReady = false;
            }
        }

        function updateAnalytics() {
            const questionCountEl = document.getElementById('questionCount');
            if (questionCountEl) {
                questionCountEl.textContent = `${questionCount} questions this session`;
            }
        }

        // Tool functions
        function bookmarkMessage(btn) {
            const messageContent = btn.closest('.message-content');
            if (!messageContent) return;
            
            const text = messageContent.textContent.replace(/📖 Save📋 Copy/g, '').trim();
            
            // Save to localStorage
            const bookmarks = JSON.parse(localStorage.getItem('phenbot_bookmarks') || '[]');
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
            if (!messageContent) return;
            
            const text = messageContent.textContent.replace(/📖 Save📋 Copy/g, '').trim();
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    btn.textContent = '📋 Copied';
                    setTimeout(() => {
                        btn.textContent = '📋 Copy';
                    }, 2000);
                });
            } else {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                
                btn.textContent = '📋 Copied';
                setTimeout(() => {
                    btn.textContent = '📋 Copy';
                }, 2000);
            }
        }

        function updateBookmarksList() {
            const bookmarksList = document.getElementById('bookmarksList');
            if (!bookmarksList) return;
            
            const bookmarks = JSON.parse(localStorage.getItem('phenbot_bookmarks') || '[]');
            
            if (bookmarks.length === 0) {
                bookmarksList.innerHTML = '<div class="bookmark-item"><div class="bookmark-title">No bookmarks yet</div><div class="bookmark-preview">Save AI responses to see them here</div></div>';
                return;
            }
            
            bookmarksList.innerHTML = bookmarks.map(bookmark => `
                <div class="bookmark-item">
                    <div class="bookmark-title">${bookmark.title}</div>
                    <div class="bookmark-preview">${bookmark.content.substring(0, 200)}${bookmark.content.length > 200 ? '...' : ''}</div>
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
            alert('Quick Quiz feature will be available soon! This will generate personalized quizzes.');
        }

        function createFlashcards() {
            if (!isSystemReady) {
                alert('AI system not ready. Please wait for connection.');
                return;
            }
            alert('Flashcard generator coming soon! Upload your notes for automatic flashcard creation.');
        }

        function generateSummary() {
            if (!isSystemReady) {
                alert('AI system not ready. Please wait for connection.');
                return;
            }
            alert('Summary generator coming soon! Get concise summaries of any topic.');
        }

        function uploadNotes() {
            alert('File upload feature coming soon! Upload PDFs, images, and documents for analysis.');
        }

        // Pomodoro timer
        let pomodoroInterval = null;
        
        document.addEventListener('DOMContentLoaded', function() {
            const pomodoroTimer = document.getElementById('pomodoroTimer');
            if (pomodoroTimer) {
                pomodoroTimer.addEventListener('click', function() {
                    if (pomodoroInterval) {
                        clearInterval(pomodoroInterval);
                        pomodoroInterval = null;
                        this.textContent = '🍅 25:00';
                        return;
                    }
                    
                    let totalSeconds = 25 * 60;
                    const timerEl = this;
                    
                    pomodoroInterval = setInterval(() => {
                        totalSeconds--;
                        const minutes = Math.floor(totalSeconds / 60);
                        const seconds = totalSeconds % 60;
                        
                        if (totalSeconds <= 0) {
                            clearInterval(pomodoroInterval);
                            pomodoroInterval = null;
                            timerEl.textContent = '🍅 Break Time!';
                            alert('Pomodoro session complete! Time for a break.');
                            setTimeout(() => {
                                timerEl.textContent = '🍅 25:00';
                            }, 3000);
                            return;
                        }
                        
                        timerEl.textContent = `🍅 ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    }, 1000);
                });
            }
        });

        // Initialize bookmarks when page loads
        setTimeout(() => {
            updateBookmarksList();
        }, 500);

        // Status check on click
        document.addEventListener('DOMContentLoaded', function() {
            const statusEl = document.getElementById('systemStatus');
            if (statusEl) {
                statusEl.addEventListener('click', checkSystemStatus);
            }
        });
    </script>
</body>
</html>"""
