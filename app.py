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
            justify-content: between;
            align-items: center;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-left: auto;
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
        }

        .send-button:hover {
            transform: scale(1.05);
        }

        /* Dashboard Cards */
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

        /* Progress Components */
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

        .bloom-chart {
            height: 200px;
            background: linear-gradient(135deg, #fef3c7, #fbbf24);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #92400e;
            font-weight: 600;
        }

        /* File Upload Area */
        .file-upload {
            border: 2px dashed var(--accent-color);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .file-upload:hover {
            background: rgba(79, 172, 254, 0.05);
        }

        .file-upload-icon {
            font-size: 48px;
            color: var(--accent-color);
            margin-bottom: 16px;
        }

        /* Study Tools */
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

        /* Bookmark Panel */
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

        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                position: absolute;
                left: -280px;
                z-index: 1000;
                height: 100vh;
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

        /* Animations */
        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .bounce {
            animation: bounce 1s ease infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
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
                <a href="#dashboard" class="nav-tab active" data-tab="dashboard">
                    <span class="nav-tab-icon">📊</span>
                    Dashboard
                </a>
                <a href="#math" class="nav-tab" data-tab="math">
                    <span class="nav-tab-icon">🔢</span>
                    Mathematics
                </a>
                <a href="#science" class="nav-tab" data-tab="science">
                    <span class="nav-tab-icon">🔬</span>
                    Science
                </a>
                <a href="#english" class="nav-tab" data-tab="english">
                    <span class="nav-tab-icon">📚</span>
                    English
                </a>
                <a href="#history" class="nav-tab" data-tab="history">
                    <span class="nav-tab-icon">🏛️</span>
                    History
                </a>
                <a href="#tools" class="nav-tab" data-tab="tools">
                    <span class="nav-tab-icon">🛠️</span>
                    Study Tools
                </a>
                <a href="#bookmarks" class="nav-tab" data-tab="bookmarks">
                    <span class="nav-tab-icon">🔖</span>
                    Bookmarks
                </a>
                <a href="#analytics" class="nav-tab" data-tab="analytics">
                    <span class="nav-tab-icon">📈</span>
                    Analytics
                </a>
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
                <div class="user-info">
                    <div class="accuracy-meter">
                        <span>Accuracy:</span>
                        <span class="accuracy-score" id="accuracyScore">92%</span>
                    </div>
                    <div class="pomodoro-timer" id="pomodoroTimer">
                        🍅 25:00
                    </div>
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
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 65%"></div>
                            </div>
                            <p>65% of daily goals completed</p>
                        </div>

                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Bloom's Analysis</div>
                                <div class="card-icon">🧠</div>
                            </div>
                            <div class="bloom-chart">
                                Skills Analysis Chart
                            </div>
                        </div>

                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Recent Activity</div>
                                <div class="card-icon">⚡</div>
                            </div>
                            <ul>
                                <li>✅ Completed Math Quiz</li>
                                <li>📖 Reviewed Science Notes</li>
                                <li>🎯 Answered 12 Questions</li>
                            </ul>
                        </div>

                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Leaderboard</div>
                                <div class="card-icon">🏆</div>
                            </div>
                            <div>
                                <p>🥇 You - 1,247 points</p>
                                <p>🥈 Alex - 1,156 points</p>
                                <p>🥉 Sam - 1,089 points</p>
                            </div>
                        </div>
                    </div>

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

                <!-- Subject-specific tabs -->
                <div class="tab-content" id="math">
                    <div class="chat-container">
                        <div class="chat-messages" id="mathMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    Welcome to Mathematics! I'm here to help you understand concepts through analogies and step-by-step explanations. What math topic would you like to explore today?
                                    <div class="message-tools">
                                        <button class="tool-btn" onclick="bookmarkMessage(this)">🔖 Save</button>
                                        <button class="tool-btn" onclick="requestAnalogy(this)">💡 Analogy</button>
                                        <button class="tool-btn" onclick="explainBack(this)">🗣️ Explain Back</button>
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
                                    <button class="input-tool" onclick="drawEquation()" title="Draw equation">✏️</button>
                                </div>
                                <button class="send-button" onclick="sendMessage('math')">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="22" y1="2" x2="11" y2="13"></line>
                                        <polygon points="22,2 15,22 11,13 2,9"></polygon>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="science">
                    <div class="chat-container">
                        <div class="chat-messages" id="scienceMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    Ready to explore Science! I can explain complex concepts using real-world analogies and help you understand the 'why' behind every phenomenon. What scientific concept interests you?
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a science question..." data-subject="science"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                    <button class="input-tool" onclick="showDiagram()" title="Show diagram">📊</button>
                                </div>
                                <button class="send-button" onclick="sendMessage('science')">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="22" y1="2" x2="11" y2="13"></line>
                                        <polygon points="22,2 15,22 11,13 2,9"></polygon>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="english">
                    <div class="chat-container">
                        <div class="chat-messages" id="englishMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    Let's dive into English & Literature! I can help with grammar, essays, poetry analysis, and creative writing. Share what you're working on!
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask about English/Literature..." data-subject="english"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                    <button class="input-tool" onclick="grammarCheck()" title="Grammar check">✓</button>
                                </div>
                                <button class="send-button" onclick="sendMessage('english')">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="22" y1="2" x2="11" y2="13"></line>
                                        <polygon points="22,2 15,22 11,13 2,9"></polygon>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="history">
                    <div class="chat-container">
                        <div class="chat-messages" id="historyMessages">
                            <div class="message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    Welcome to History! I'll help you understand historical events through engaging stories and timelines. What period or event would you like to explore?
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="message-input" placeholder="Ask a history question..." data-subject="history"></textarea>
                                <div class="input-tools">
                                    <button class="input-tool" onclick="uploadFile()" title="Upload file">📁</button>
                                    <button class="input-tool" onclick="voiceInput()" title="Voice input">🎤</button>
                                    <button class="input-tool" onclick="showTimeline()" title="Timeline">📅</button>
                                </div>
                                <button class="send-button" onclick="sendMessage('history')">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="22" y1="2" x2="11" y2="13"></line>
                                        <polygon points="22,2 15,22 11,13 2,9"></polygon>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="tools">
                    <h2 style="margin-bottom: 24px;">Study Tools & Resources</h2>
                    
                    <div class="file-upload" onclick="uploadSyllabus()">
                        <div class="file-upload-icon">📄</div>
                        <h3>Upload Syllabus</h3>
                        <p>Upload your syllabus and I'll fetch relevant textbooks and resources</p>
                    </div>

                    <div class="study-tools">
                        <div class="study-tool" onclick="createFlowchart()">
                            <div class="study-tool-icon">📊</div>
                            <h3>Flowchart Maker</h3>
                            <p>Convert notes to visual flowcharts</p>
                        </div>
                        <div class="study-tool" onclick="flashcardGenerator()">
                            <div class="study-tool-icon">🗂️</div>
                            <h3>Flashcard Generator</h3>
                            <p>Auto-generate flashcards from content</p>
                        </div>
                        <div class="study-tool" onclick="quizMaker()">
                            <div class="study-tool-icon">❓</div>
                            <h3>Quiz Maker</h3>
                            <p>Create personalized quizzes</p>
                        </div>
                        <div class="study-tool" onclick="studyScheduler()">
                            <div class="study-tool-icon">📅</div>
                            <h3>Study Scheduler</h3>
                            <p>Plan your study sessions</p>
                        </div>
                        <div class="study-tool" onclick="reverseMode()">
                            <div class="study-tool-icon">🔄</div>
                            <h3>Reverse Learning</h3>
                            <p>Teach the bot and find gaps</p>
                        </div>
                        <div class="study-tool" onclick="mindfulBreaks()">
                            <div class="study-tool-icon">🧘</div>
                            <h3>Mindful Breaks</h3>
                            <p>Guided relaxation exercises</p>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="bookmarks">
                    <h2 style="margin-bottom: 24px;">Saved Answers & Bookmarks</h2>
                    <div id="bookmarksList">
                        <div class="bookmark-item">
                            <div class="bookmark-title">Quadratic Formula Explanation</div>
                            <div class="bookmark-preview">The quadratic formula is used to solve equations of the form ax² + bx + c = 0...</div>
                        </div>
                        <div class="bookmark-item">
                            <div class="bookmark-title">Newton's Laws of Motion</div>
                            <div class="bookmark-preview">Newton's first law states that an object at rest stays at rest...</div>
                        </div>
                    </div>
                </div>

                <div class="tab-content" id="analytics">
                    <h2 style="margin-bottom: 24px;">Learning Analytics</h2>
                    <div class="dashboard-grid">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <div class="card-title">Bloom's Taxonomy Analysis</div>
                                <div class="card-icon">🧠</div>
                            </div
