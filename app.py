# Main App HTML Template with Enhanced Features - COMPLETE VERSION
MAIN_APP_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT - AI Study Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .user-name {
            font-weight: 500;
        }
        
        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
            text-decoration: none;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        /* Main Container */
        .main-container {
            display: flex;
            margin-top: 80px;
            min-height: calc(100vh - 80px);
        }
        
        /* Sidebar */
        .sidebar {
            width: 350px;
            background: white;
            box-shadow: 4px 0 20px rgba(0,0,0,0.1);
            padding: 2rem 1rem;
            overflow-y: auto;
            border-radius: 0 20px 0 0;
        }
        
        .sidebar-section {
            margin-bottom: 2rem;
        }
        
        .sidebar-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #333;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Chat Area */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
            margin: 1rem;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-title {
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .chat-controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        /* Chat Messages */
        .chat-messages {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
            max-height: 500px;
            background: #f8fafc;
        }
        
        .message {
            margin-bottom: 1.5rem;
            animation: fadeIn 0.3s ease-in;
        }
        
        .message-user {
            text-align: right;
        }
        
        .message-content {
            display: inline-block;
            max-width: 80%;
            padding: 1rem 1.5rem;
            border-radius: 20px;
            word-wrap: break-word;
        }
        
        .message-user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .message-bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #e1e5e9;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .message-info {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Chat Input */
        .chat-input {
            padding: 2rem;
            background: white;
            border-top: 1px solid #e1e5e9;
        }
        
        .input-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .input-field {
            flex: 1;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 1rem;
            resize: none;
            min-height: 60px;
            transition: border-color 0.3s;
        }
        
        .input-field:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .send-btn {
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .send-btn:hover:not(:disabled) {
            transform: translateY(-2px);
        }
        
        .send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        /* Controls */
        .controls-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
        }
        
        .control-label {
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #555;
        }
        
        .control-select {
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            background: white;
            font-size: 0.9rem;
            transition: border-color 0.3s;
        }
        
        .control-select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        /* Pomodoro Timer */
        .pomodoro-timer {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .timer-display {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            font-family: 'Courier New', monospace;
        }
        
        .timer-controls {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
            margin-bottom: 0.5rem;
        }
        
        .timer-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: background 0.3s;
        }
        
        .timer-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .timer-status {
            font-size: 0.9rem;
            margin-top: 0.5rem;
            opacity: 0.9;
        }
        
        /* File Upload */
        .file-upload {
            margin-bottom: 1rem;
        }
        
        .file-drop-zone {
            border: 2px dashed #667eea;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            background: #f8fafc;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .file-drop-zone:hover {
            background: #f1f5f9;
            border-color: #4c63d2;
        }
        
        .file-drop-zone.drag-over {
            background: #e0e7ff;
            border-color: #3b82f6;
        }
        
        .file-input {
            display: none;
        }
        
        .file-info {
            margin-top: 1rem;
            padding: 1rem;
            background: #e0f2fe;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        
        /* Flashcards */
        .flashcard {
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .flashcard:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .flashcard.flipped {
            background: #f0f9ff;
            border-color: #0ea5e9;
        }
        
        .flashcard-content {
            font-size: 1.1rem;
            line-height: 1.5;
            text-align: center;
        }
        
        .flashcard-hint {
            font-size: 0.8rem;
            color: #666;
            text-align: center;
            margin-top: 1rem;
            font-style: italic;
        }
        
        /* Buttons */
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Voice Chat */
        .voice-controls {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        .voice-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .voice-btn:hover {
            transform: scale(1.1);
        }
        
        .voice-btn.recording {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            animation: pulse 1s infinite;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        /* Loading States */
        .loading {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #e1e5e9;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .sidebar {
                width: 280px;
            }
        }
        
        @media (max-width: 768px) {
            .header-content {
                padding: 0 1rem;
            }
            
            .main-container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                padding: 1rem;
                border-radius: 0;
            }
            
            .chat-area {
                margin: 0.5rem;
                border-radius: 15px;
            }
            
            .controls-row {
                grid-template-columns: 1fr;
            }
        }
        
        /* Success/Error Messages */
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        .alert-info {
            background: #e0f2fe;
            color: #0c4a6e;
            border: 1px solid #7dd3fc;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 2px solid #e1e5e9;
            margin-bottom: 1rem;
        }
        
        .tab {
            padding: 0.75rem 1.5rem;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom: 2px solid #667eea;
        }
        
        .tab:hover {
            color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }

        /* Modal Overlay */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 2000;
            padding: 2rem;
        }

        .modal-content {
            background: white;
            border-radius: 20px;
            max-width: 800px;
            margin: 0 auto;
            height: 80vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .modal-header {
            padding: 2rem;
            border-bottom: 1px solid #e1e5e9;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-body {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
        }

        .close-btn {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <div class="logo">
                🤖 PhenBOT
            </div>
            <div class="user-info">
                <span class="user-name">Welcome, {{ username }}!</span>
                <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <!-- Pomodoro Timer -->
            <div class="sidebar-section">
                <div class="sidebar-title">🍅 Focus Timer</div>
                <div class="pomodoro-timer">
                    <div class="timer-display" id="timerDisplay">25:00</div>
                    <div class="timer-controls">
                        <button class="timer-btn" onclick="startTimer()">Start</button>
                        <button class="timer-btn" onclick="pauseTimer()">Pause</button>
                        <button class="timer-btn" onclick="resetTimer()">Reset</button>
                    </div>
                    <div class="timer-status" id="timerStatus">Ready to focus</div>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="sidebar-section">
                <div class="sidebar-title">📊 Today's Stats</div>
                <div style="background: white; padding: 1rem; border-radius: 10px; font-size: 0.9rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Questions Asked:</span>
                        <span id="questionsToday">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span>Study Time:</span>
                        <span id="studyTime">0m</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Flashcards Created:</span>
                        <span id="flashcardsToday">0</span>
                    </div>
                </div>
            </div>

            <!-- File Upload -->
            <div class="sidebar-section">
                <div class="sidebar-title">📄 Upload Document</div>
                <div class="file-upload">
                    <div class="file-drop-zone" onclick="document.getElementById('fileInput').click()">
                        <p>📁 Drop PDF file here or click to browse</p>
                        <p style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">PDF, TXT files supported</p>
                    </div>
                    <input type="file" id="fileInput" class="file-input" accept=".pdf,.txt" onchange="handleFileUpload(event)">
                    <div id="fileInfo" class="file-info" style="display: none;"></div>
                </div>
            </div>

            <!-- Flashcard Generator -->
            <div class="sidebar-section">
                <div class="sidebar-title">🎴 Flashcard Generator</div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <button class="btn btn-primary" onclick="openFlashcardModal('topic')">Create from Topic</button>
                    <button class="btn btn-secondary" onclick="openFlashcardModal('file')" id="createFromFileBtn" disabled>Create from File</button>
                    <button class="btn btn-secondary" onclick="viewSavedFlashcards()">View Saved Cards</button>
                </div>
            </div>
        </div>
        
        <!-- Chat Area -->
        <div class="chat-area">
            <div class="chat-header">
                <div class="chat-title">AI Study Assistant</div>
                <div class="chat-controls">
                    <div class="voice-controls">
                        <button class="voice-btn" id="voiceBtn" onclick="toggleVoiceRecording()" title="Voice Input">
                            🎤
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message message-bot">
                    <div class="message-content">
                        Welcome to PhenBOT! I'm your AI study assistant. I can help you with various subjects using different teaching modes. How can I assist you today?
                    </div>
                    <div class="message-info">
                        <span>🤖 Bot</span>
                        <span>•</span>
                        <span>Just now</span>
                    </div>
                </div>
            </div>
            
            <div class="chat-input">
                <div class="controls-row">
                    <div class="control-group">
                        <label class="control-label">Subject</label>
                        <select class="control-select" id="subjectSelect">
                            <option value="general">General</option>
                            <option value="math">Mathematics</option>
                            <option value="science">Science</option>
                            <option value="english">English & Literature</option>
                            <option value="history">History</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Teaching Mode</label>
                        <select class="control-select" id="modeSelect">
                            <option value="normal">Normal</option>
                            <option value="analogy">Analogy & Examples</option>
                            <option value="quiz">Quiz Mode</option>
                            <option value="teach">Step-by-Step</option>
                            <option value="socratic">Socratic Method</option>
                            <option value="summary">Summary</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Response Length</label>
                        <select class="control-select" id="lengthSelect">
                            <option value="normal">Normal</option>
                            <option value="short">Short</option>
                            <option value="detailed">Detailed</option>
                        </select>
                    </div>
                </div>
                
                <div class="input-group">
                    <textarea class="input-field" id="messageInput" placeholder="Ask me anything about your studies..." rows="3"></textarea>
                    <button class="send-btn" id="sendBtn" onclick="sendMessage()" disabled>
                        <span>Send</span>
                        <span>📤</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Flashcard Modal -->
    <div class="modal-overlay" id="flashcardModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Generate Flashcards</h2>
                <button class="close-btn" onclick="closeFlashcardModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div id="flashcardForm">
                    <div class="control-group" style="margin-bottom: 1rem;">
                        <label class="control-label">Topic (for topic-based generation)</label>
                        <input type="text" id="topicInput" placeholder="e.g., Photosynthesis, World War II, Algebra" style="width: 100%; padding: 0.75rem; border: 2px solid #e1e5e9; border-radius: 8px;">
                    </div>
                    <div class="controls-row">
                        <div class="control-group">
                            <label class="control-label">Subject</label>
                            <select class="control-select" id="flashcardSubject">
                                <option value="general">General</option>
                                <option value="math">Mathematics</option>
                                <option value="science">Science</option>
                                <option value="english">English</option>
                                <option value="history">History</option>
                            </select>
                        </div>
                        <div class="control-group">
                            <label class="control-label">Difficulty</label>
                            <select class="control-select" id="flashcardDifficulty">
                                <option value="easy">Easy</option>
                                <option value="medium">Medium</option>
                                <option value="hard">Hard</option>
                            </select>
                        </div>
                        <div class="control-group">
                            <label class="control-label">Number of Cards</label>
                            <select class="control-select" id="flashcardCount">
                                <option value="3">3 Cards</option>
                                <option value="5" selected>5 Cards</option>
                                <option value="8">8 Cards</option>
                                <option value="10">10 Cards</option>
                            </select>
                        </div>
                    </div>
                    <div style="margin: 1rem 0;">
                        <button class="btn btn-primary" onclick="generateFlashcards()">Generate Flashcards</button>
                    </div>
                </div>
                
                <div id="flashcardPreview" style="display: none;">
                    <div style="margin-bottom: 1rem; display: flex; gap: 1rem; align-items: center;">
                        <button class="btn btn-success" onclick="saveAllFlashcards()">Save All Cards</button>
                        <button class="btn btn-secondary" onclick="showFlashcardForm()">Generate New</button>
                        <span id="flashcardCounter" style="color: #666;"></span>
                    </div>
                    <div id="flashcardContainer"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let currentFileId = null;
        let pomodoroTimer = null;
        let pomodoroSeconds = 25 * 60; // 25 minutes
        let isTimerRunning = false;
        let currentFlashcards = [];
        let flashcardGenerationType = 'topic';
        let questionsAskedToday = 0;
        let studyTimeMinutes = 0;
        let flashcardsCreatedToday = 0;
        let recognition = null;
        let isRecording = false;

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
        });

        function initializeApp() {
            setupEventListeners();
            initializeVoiceRecognition();
            loadTodayStats();
            updateTimerDisplay();
        }

        function setupEventListeners() {
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            
            messageInput.addEventListener('input', function() {
                sendBtn.disabled = this.value.trim() === '';
            });
            
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (this.value.trim() !== '') {
                        sendMessage();
                    }
                }
            });

            // File drop zone
            const dropZone = document.querySelector('.file-drop-zone');
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('drag-over');
            });
            
            dropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.classList.remove('drag-over');
            });
            
            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileUpload({target: {files: files}});
                }
            });
        }

        // Chat functionality
        async function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            const subject = document.getElementById('subjectSelect').value;
            const mode = document.getElementById('modeSelect').value;
            const length = document.getElementById('lengthSelect').value;
            
            // Add user message to chat
            addMessageToChat(message, 'user');
            messageInput.value = '';
            document.getElementById('sendBtn').disabled = true;
            
            // Show loading
            const loadingId = addMessageToChat('Thinking...', 'bot', true);
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: message,
                        subject: subject,
                        mode: mode,
                        length: length
                    })
                });
                
                const data = await response.json();
                
                // Remove loading message
                document.getElementById(loadingId).remove();
                
                if (data.error) {
                    addMessageToChat('Sorry, there was an error: ' + data.error, 'bot');
                } else {
                    addMessageToChat(data.answer, 'bot');
                    questionsAskedToday++;
                    updateTodayStats();
                }
                
            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessageToChat('Sorry, there was a connection error. Please try again.', 'bot');
            }
        }

        function addMessageToChat(content, sender, isLoading = false) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const messageId = 'msg_' + Date.now();
            messageDiv.id = messageId;
            messageDiv.className = `message message-${sender}`;
            
            const now = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = `
                <div class="message-content">${content}${isLoading ? ' <div class="spinner"></div>' : ''}</div>
                <div class="message-info">
                    <span>${sender === 'user' ? '👤 You' : '🤖 Bot'}</span>
                    <span>•</span>
                    <span>${now}</span>
                </div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            return messageId;
        }

        // File upload functionality
        async function handleFileUpload(event) {
            const files = event.target.files;
            if (files.length === 0) return;
            
            const file = files[0];
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                alert('Please upload a PDF file.');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const fileInfo = document.getElementById('fileInfo');
            fileInfo.style.display = 'block';
            fileInfo.innerHTML = '<div class="loading"><div class="spinner"></div>Uploading...</div>';
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentFileId = data.file_id;
                    fileInfo.innerHTML = `
                        <strong>✅ File uploaded successfully!</strong><br>
                        <strong>File:</strong> ${data.filename}<br>
                        <strong>Text extracted:</strong> ${data.text_extracted ? 'Yes' : 'No'}<br>
                        ${data.text_length ? `<strong>Text length:</strong> ${data.text_length} characters` : ''}
                        <div style="margin-top: 0.5rem;">
                            <button class="btn btn-primary" onclick="summarizePDF()" style="margin-right: 0.5rem;">Summarize</button>
                            <button class="btn btn-secondary" onclick="enableFileFlashcards()">Create Flashcards</button>
                        </div>
                    `;
                } else {
                    fileInfo.innerHTML = `<strong>❌ Upload failed:</strong> ${data.error}`;
                }
                
            } catch (error) {
                fileInfo.innerHTML = '<strong>❌ Upload failed:</strong> Connection error';
            }
        }

        function enableFileFlashcards() {
            document.getElementById('createFromFileBtn').disabled = false;
            document.getElementById('createFromFileBtn').textContent = 'Create from Uploaded File';
        }

        async function summarizePDF() {
            if (!currentFileId) return;
            
            const loadingId = addMessageToChat('Summarizing your PDF...', 'bot', true);
            
            try {
                const response = await fetch('/api/summarize_pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        file_id: currentFileId
                    })
                });
                
                const data = await response.json();
                
                document.getElementById(loadingId).remove();
                
                if (data.error) {
                    addMessageToChat('Error summarizing PDF: ' + data.error, 'bot');
                } else {
                    addMessageToChat('📄 **PDF Summary:**\n\n' + data.summary, 'bot');
                }
                
            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessageToChat('Error summarizing PDF: Connection error', 'bot');
            }
        }

        // Pomodoro Timer Functions
        function updateTimerDisplay() {
            const minutes = Math.floor(pomodoroSeconds / 60);
            const seconds = pomodoroSeconds % 60;
            document.getElementById('timerDisplay').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        function startTimer() {
            if (isTimerRunning) return;
            
            isTimerRunning = true;
            document.getElementById('timerStatus').textContent = 'Focusing...';
            
            pomodoroTimer = setInterval(() => {
                pomodoroSeconds--;
                updateTimerDisplay();
                
                if (pomodoroSeconds <= 0) {
                    clearInterval(pomodoroTimer);
                    isTimerRunning = false;
                    document.getElementById('timerStatus').textContent = 'Break time!';
                    studyTimeMinutes += 25;
                    updateTodayStats();
                    alert('🎉 Great job! Time for a 5-minute break.');
                    pomodoroSeconds = 5 * 60; // 5-minute break
                    updateTimerDisplay();
                }
            }, 1000);
        }

        function pauseTimer() {
            if (pomodoroTimer) {
                clearInterval(pomodoroTimer);
                pomodoroTimer = null;
                isTimerRunning = false;
                document.getElementById('timerStatus').textContent = 'Paused';
            }
        }

        function resetTimer() {
            if (pomodoroTimer) {
                clearInterval(pomodoroTimer);
                pomodoroTimer = null;
            }
            isTimerRunning = false;
            pomodoroSeconds = 25 * 60;
            updateTimerDisplay();
            document.getElementById('timerStatus').textContent = 'Ready to focus';
        }

        // Voice Recognition
        function initializeVoiceRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('messageInput').value = transcript;
                    document.getElementById('sendBtn').disabled = false;
                };

                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                };

                recognition.onend = function() {
                    isRecording = false;
                    document.getElementById('voiceBtn').classList.remove('recording');
                    document.getElementById('voiceBtn').textContent = '🎤';
                };
            }
        }

        function toggleVoiceRecording() {
            if (!recognition) {
                alert('Speech recognition is not supported in your browser.');
                return;
            }

            if (isRecording) {
                recognition.stop();
            } else {
                isRecording = true;
                document.getElementById('voiceBtn').classList.add('recording');
                document.getElementById('voiceBtn').textContent = '🛑';
                recognition.start();
            }
        }

        // Flashcard Functions
        function openFlashcardModal(type) {
            flashcardGenerationType = type;
            document.getElementById('flashcardModal').style.display = 'block';
            
            if (type === 'file') {
                document.getElementById('modalTitle').textContent = 'Generate Flashcards from Uploaded File';
                document.getElementById('topicInput').style.display = 'none';
                document.getElementById('topicInput').previousElementSibling.style.display = 'none';
            } else {
                document.getElementById('modalTitle').textContent = 'Generate Flashcards from Topic';
                document.getElementById('topicInput').style.display = 'block';
                document.getElementById('topicInput').previousElementSibling.style.display = 'block';
            }
            
            showFlashcardForm();
        }

        function closeFlashcardModal() {
            document.getElementById('flashcardModal').style.display = 'none';
            currentFlashcards = [];
        }

        function showFlashcardForm() {
            document.getElementById('flashcardForm').style.display = 'block';
            document.getElementById('flashcardPreview').style.display = 'none';
        }

        async function generateFlashcards() {
            const topic = document.getElementById('topicInput').value.trim();
            const subject = document.getElementById('flashcardSubject').value;
            const difficulty = document.getElementById('flashcardDifficulty').value;
            const count = parseInt(document.getElementById('flashcardCount').value);

            if (flashcardGenerationType === 'topic' && !topic) {
                alert('Please enter a topic.');
                return;
            }

            if (flashcardGenerationType === 'file' && !currentFileId) {
                alert('Please upload a file first.');
                return;
            }

            // Show loading
            document.getElementById('flashcardForm').style.display = 'none';
            document.getElementById('flashcardPreview').style.display = 'block';
            document.getElementById('flashcardContainer').innerHTML = '<div class="loading"><div class="spinner"></div>Generating flashcards...</div>';

            try {
                const requestBody = {
                    source_type: flashcardGenerationType,
                    subject: subject,
                    difficulty: difficulty,
                    count: count
                };

                if (flashcardGenerationType === 'topic') {
                    requestBody.topic = topic;
                } else {
                    requestBody.file_id = currentFileId;
                }

                const response = await fetch('/api/generate_flashcards', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                if (data.error) {
                    document.getElementById('flashcardContainer').innerHTML = `<div class="alert alert-error">${data.error}</div>`;
                    return;
                }

                currentFlashcards = data.flashcards;
                displayFlashcards(data.flashcards);
                document.getElementById('flashcardCounter').textContent = `${data.flashcards.length} cards generated`;

            } catch (error) {
                document.getElementById('flashcardContainer').innerHTML = '<div class="alert alert-error">Error generating flashcards. Please try again.</div>';
            }
        }

        function displayFlashcards(flashcards) {
            const container = document.getElementById('flashcardContainer');
            
            if (flashcards.length === 0) {
                container.innerHTML = '<div class="alert alert-info">No flashcards generated. Try a different topic or settings.</div>';
                return;
            }

            container.innerHTML = flashcards.map((card, index) => `
                <div class="flashcard" id="card_${index}" onclick="flipCard(${index})">
                    <div class="flashcard-content" id="cardContent_${index}">
                        ${card.front}
                    </div>
                    <div class="flashcard-hint">Click to flip</div>
                </div>
            `).join('');
        }

        function flipCard(index) {
            const card = document.getElementById(`card_${index}`);
            const content = document.getElementById(`cardContent_${index}`);
            const isFlipped = card.classList.contains('flipped');

            if (isFlipped) {
                card.classList.remove('flipped');
                content.textContent = currentFlashcards[index].front;
            } else {
                card.classList.add('flipped');
                content.textContent = currentFlashcards[index].back;
            }
        }

        async function saveAllFlashcards() {
            if (currentFlashcards.length === 0) return;

            const title = prompt('Enter a title for this flashcard set:', `Flashcards - ${new Date().toLocaleDateString()}`);
            if (!title) return;

            const subject = document.getElementById('flashcardSubject').value;
            const difficulty = document.getElementById('flashcardDifficulty').value;

            try {
                const promises = currentFlashcards.map(card => 
                    fetch('/api/save_flashcard', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            title: title,
                            front: card.front,
                            back: card.back,
                            subject: subject,
                            difficulty: difficulty
                        })
                    })
                );

                await Promise.all(promises);
                alert('Flashcards saved successfully!');
                flashcardsCreatedToday += currentFlashcards.length;
                updateTodayStats();
                closeFlashcardModal();

            } catch (error) {
                alert('Error saving flashcards. Please try again.');
            }
        }

        async function viewSavedFlashcards() {
            try {
                const response = await fetch('/api/get_flashcards');
                const data = await response.json();

                if (data.error) {
                    alert('Error loading flashcards: ' + data.error);
                    return;
                }

                if (data.flashcards.length === 0) {
                    alert('No saved flashcards found. Create some flashcards first!');
                    return;
                }

                // Display in modal
                document.getElementById('modalTitle').textContent = 'Saved Flashcards';
                document.getElementById('flashcardForm').style.display = 'none';
                document.getElementById('flashcardPreview').style.display = 'block';
                
                const container = document.getElementById('flashcardContainer');
                container.innerHTML = data.flashcards.map((card, index) => `
                    <div class="flashcard" onclick="flipSavedCard(${index}, '${card.front}', '${card.back}')">
                        <div class="flashcard-content" id="savedCardContent_${index}">
                            ${card.front}
                        </div>
                        <div class="flashcard-hint">
                            <strong>${card.title}</strong> • ${card.subject} • ${card.difficulty}<br>
                            Created: ${new Date(card.created_at).toLocaleDateString()}
                        </div>
                    </div>
                `).join('');

                document.getElementById('flashcardCounter').textContent = `${data.flashcards.length} saved cards`;
                document.getElementById('flashcardModal').style.display = 'block';

            } catch (error) {
                alert('Error loading flashcards: Connection error');
            }
        }

        function flipSavedCard(index, front, back) {
            const card = document.getElementById(`savedCardContent_${index}`);
            const isFlipped = card.dataset.flipped === 'true';

            if (isFlipped) {
                card.textContent = front;
                card.dataset.flipped = 'false';
                card.parentElement.classList.remove('flipped');
            } else {
                card.textContent = back;
                card.dataset.flipped = 'true';
                card.parentElement.classList.add('flipped');
            }
        }

        // Stats Functions
        function loadTodayStats() {
            const today = new Date().toDateString();
            const savedStats = localStorage.getItem('phenbot_stats_' + today);
            
            if (savedStats) {
                const stats = JSON.parse(savedStats);
                questionsAskedToday = stats.questions || 0;
                studyTimeMinutes = stats.studyTime || 0;
                flashcardsCreatedToday = stats.flashcards || 0;
                updateTodayStats();
            }
        }

        function updateTodayStats() {
            document.getElementById('questionsToday').textContent = questionsAskedToday;
            document.getElementById('studyTime').textContent = studyTimeMinutes + 'm';
            document.getElementById('flashcardsToday').textContent = flashcardsCreatedToday;

            // Save to localStorage
            const today = new Date().toDateString();
            const stats = {
                questions: questionsAskedToday,
                studyTime: studyTimeMinutes,
                flashcards: flashcardsCreatedToday
            };
            localStorage.setItem('phenbot_stats_' + today, JSON.stringify(stats));
        }

        // Click outside modal to close
        window.addEventListener('click', function(event) {
            const modal = document.getElementById('flashcardModal');
            if (event.target === modal) {
                closeFlashcardModal();
            }
        });
    </script>
</body>
</html>
'''

# Main Routes
@app.route('/')
def index():
    if is_logged_in():
        return render_template_string(MAIN_APP_HTML, 
                                    username=session['username'],
                                    datetime=datetime)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
        else:
            user = get_user(username)
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Successfully logged in!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
    
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
        elif len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
        else:
            if create_user(username, password):
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Username already exists', 'error')
    
    return render_template_string(REGISTER_HTML)

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

# API Endpoints
@app.route('/health')
def health():
    return jsonify({
        'healthy': True,
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(os.environ.get('GROQ_API_KEY')),
        'error': GROQ_ERROR,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/ask', methods=['POST'])
@require_login
def api_ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        question = data.get('question', '').strip()
        subject = data.get('subject', 'general')
        mode = data.get('mode', 'normal')
        length_preference = data.get('length', 'normal')
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'AI system unavailable: {GROQ_ERROR}'}), 503
        
        # Get AI response
        answer = get_ai_response(question, subject, mode, length_preference)
        
        # Save to chat history
        save_chat_history(session['user_id'], subject, mode, length_preference, question, answer)
        
        return jsonify({
            'answer': answer,
            'mode': mode,
            'length': length_preference,
            'subject': subject
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/api/upload', methods=['POST'])
@require_login
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        unique_filename = timestamp + filename
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Extract text if PDF
        extracted_text = None
        if filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)
        
        # Save file info to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploaded_files (user_id, filename, original_filename, file_path, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], unique_filename, filename, file_path, 
              filename.rsplit('.', 1)[1].lower()))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'text_extracted': bool(extracted_text),
            'text_length': len(extracted_text) if extracted_text else 0
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/summarize_pdf', methods=['POST'])
@require_login
def summarize_pdf():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({'error': 'File ID required'}), 400
        
        # Get file info
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM uploaded_files WHERE id = ? AND user_id = ?', 
                      (file_id, session['user_id']))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'File not found'}), 404
        
        # Extract text
        text = extract_text_from_pdf(result[0])
        if not text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Generate summary
        summary_prompt = f"Provide a comprehensive summary of this document:\n\n{text[:3000]}..."
        summary = get_ai_response(summary_prompt, 'general', 'summary', 'detailed')
        
        return jsonify({
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary)
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Summarization failed'}), 500

@app.route('/api/generate_flashcards', methods=['POST'])
@require_login
def api_generate_flashcards():
    try:
        data = request.get_json()
        source_type = data.get('source_type', 'topic')  # 'topic' or 'file'
        
        if source_type == 'file':
            file_id = data.get('file_id')
            if not file_id:
                return jsonify({'error': 'File ID required'}), 400
            
            # Get file and extract text
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM uploaded_files WHERE id = ? AND user_id = ?', 
                          (file_id, session['user_id']))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return jsonify({'error': 'File not found'}), 404
            
            text = extract_text_from_pdf(result[0])
            if not text:
                return jsonify({'error': 'Could not extract text from file'}), 400
            
            subject = data.get('subject', 'general')
            difficulty = data.get('difficulty', 'medium')
            count = min(data.get('count', 5), 10)  # Max 10 flashcards
            
            flashcards = generate_flashcards_from_text(text, subject, difficulty, count)
            
        else:  # topic-based
            topic = data.get('topic', '').strip()
            if not topic:
                return jsonify({'error': 'Topic required'}), 400
            
            subject = data.get('subject', 'general')
            difficulty = data.get('difficulty', 'medium')
            count = min(data.get('count', 5), 10)
            
            flashcards = generate_flashcards_from_topic(topic, subject, difficulty, count)
        
        # Save flashcards if requested
        if data.get('save_flashcards', False):
            title = data.get('title', f"Flashcards - {datetime.now().strftime('%Y-%m-%d')}")
            for card in flashcards:
                save_flashcard(session['user_id'], title, card['front'], card['back'], 
                             subject, difficulty)
        
        return jsonify({
            'flashcards': flashcards,
            'count': len(flashcards)
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Flashcard generation failed'}), 500

@app.route('/api/save_flashcard', methods=['POST'])
@require_login
def api_save_flashcard():
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        front = data.get('front', '').strip()
        back = data.get('back', '').strip()
        subject = data.get('subject', 'general')
        difficulty = data.get('difficulty', 'medium')
        
        if not front or not back:
            return jsonify({'error': 'Front and back content required'}), 400
        
        if save_flashcard(session['user_id'], title, front, back, subject, difficulty):
            return jsonify({'success': True, 'message': 'Flashcard saved successfully'})
        else:
            return jsonify({'error': 'Failed to save flashcard'}), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Save failed'}), 500

@app.route('/api/get_flashcards')
@require_login
def api_get_flashcards():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, front, back, subject, difficulty, created_at
            FROM flashcards WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 50
        ''', (session['user_id'],))
        
        flashcards = []
        for row in cursor.fetchall():
            flashcards.append({
                'id': row[0],
                'title': row[1],
                'front': row[2],
                'back': row[3],
                'subject': row[4],
                'difficulty': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return jsonify({'flashcards': flashcards})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Failed to load flashcards'}), 500

@app.route('/api/chat_history')
@require_login
def api_chat_history():
    try:
        subject = request.args.get('subject', None)
        limit = min(int(request.args.get('limit', 20)), 100)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        if subject:
            cursor.execute('''
                SELECT question, answer, mode, length_preference, timestamp
                FROM chat_history WHERE user_id = ? AND subject = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (session['user_id'], subject, limit))
        else:
            cursor.execute('''
                SELECT question, answer, mode, length_preference, timestamp, subject
                FROM chat_history WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (session['user_id'], limit))
        
        history = []
        for row in cursor.fetchall():
            item = {
                'question': row[0],
                'answer': row[1],
                'mode': row[2],
                'length': row[3],
                'timestamp': row[4]
            }
            if not subject:
                item['subject'] = row[5]
            history.append(item)
        
        conn.close()
        return jsonify({'history': history})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Failed to load chat history'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return redirect(url_for('login'))

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Enhanced PhenBOT on port {port}")
    print(f"Groq available: {GROQ_AVAILABLE}")
    if GROQ_ERROR:
        print(f"Groq error: {GROQ_ERROR}")
    app.run(host='0.0.0.0', port=port, debug=False)from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import traceback
import PyPDF2
import io
import base64
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database setup
DATABASE = 'phenbot.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    """Initialize database with enhanced tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chat history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            mode TEXT,
            length_preference TEXT,
            question TEXT,
            answer TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Uploaded files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            original_filename TEXT,
            file_path TEXT,
            file_type TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Flashcards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            front TEXT,
            back TEXT,
            subject TEXT,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text content from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def get_user(username):
    """Get user by username"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    """Create a new user"""
    try:
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      (username, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def save_chat_history(user_id, subject, mode, length_preference, question, answer):
    """Save chat interaction to database"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (user_id, subject, mode, length_preference, question, answer)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, subject, mode, length_preference, question, answer))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving chat history: {e}")

def save_flashcard(user_id, title, front, back, subject, difficulty):
    """Save flashcard to database"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO flashcards (user_id, title, front, back, subject, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, front, back, subject, difficulty))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving flashcard: {e}")
        return False

init_db()

# Groq AI Setup
try:
    from groq import Groq
    GROQ_IMPORT_SUCCESS = True
except ImportError:
    GROQ_IMPORT_SUCCESS = False

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """Initialize Groq client"""
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    
    if not GROQ_IMPORT_SUCCESS:
        GROQ_ERROR = 'Groq SDK not installed'
        GROQ_AVAILABLE = False
        return
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        GROQ_ERROR = 'GROQ_API_KEY environment variable missing'
        GROQ_AVAILABLE = False
        return
    
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
    except Exception as e:
        GROQ_ERROR = str(e)
        GROQ_AVAILABLE = False
        print(f"Groq initialization failed: {e}")

initialize_groq()

def get_ai_response(question, subject, mode, length_preference, context=None):
    """Enhanced AI response with modes and length preferences"""
    if not groq_client:
        return "AI system is currently unavailable. Please check the server configuration."
    
    # Base system prompts for subjects
    subject_prompts = {
        'math': 'You are PhenBOT, a mathematics tutor.',
        'science': 'You are PhenBOT, a science educator.',  
        'english': 'You are PhenBOT, an English and literature tutor.',
        'history': 'You are PhenBOT, a history educator.',
        'general': 'You are PhenBOT, an AI study assistant.'
    }
    
    # Mode-specific instructions
    mode_instructions = {
        'normal': 'Provide clear, direct explanations.',
        'analogy': 'Explain concepts using creative analogies and real-world comparisons. Make complex ideas easier to understand through relatable examples.',
        'quiz': 'Create engaging quiz questions based on the topic. Provide multiple choice or short answer questions with explanations.',
        'teach': 'Act as a patient teacher. Break down concepts step-by-step, check for understanding, and provide practice examples.',
        'socratic': 'Use the Socratic method - guide learning through thoughtful questions rather than direct answers.',
        'summary': 'Provide concise summaries and key points. Focus on the most important information.'
    }
    
    # Length preferences
    length_instructions = {
        'short': 'Keep your response concise - 2-3 sentences maximum.',
        'normal': 'Provide a moderate length response - 1-2 paragraphs.',
        'detailed': 'Give a comprehensive, detailed explanation with examples and additional context.'
    }
    
    # Build the system prompt
    base_prompt = subject_prompts.get(subject, subject_prompts['general'])
    mode_instruction = mode_instructions.get(mode, mode_instructions['normal'])
    length_instruction = length_instructions.get(length_preference, length_instructions['normal'])
    
    system_prompt = f"{base_prompt} {mode_instruction} {length_instruction}"
    
    # Add context if provided (for PDF processing)
    if context:
        system_prompt += f" Use this context to inform your response: {context[:1000]}..."
    
    try:
        # Adjust max_tokens based on length preference
        token_limits = {
            'short': 150,
            'normal': 400, 
            'detailed': 800
        }
        
        max_tokens = token_limits.get(length_preference, 400)
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return f"Error processing your question: {str(e)}"

def generate_flashcards_from_text(text, subject, difficulty, count=5):
    """Generate flashcards from text content"""
    if not groq_client:
        return []
    
    prompt = f"""
    Create {count} flashcards from the following text for {subject} at {difficulty} difficulty level.
    
    Text: {text[:2000]}...
    
    Format each flashcard as:
    FRONT: [Question or concept]
    BACK: [Answer or explanation]
    ---
    
    Make the flashcards educational and appropriate for the difficulty level.
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        
        content = response.choices[0].message.content
        flashcards = []
        
        # Parse the response into flashcards
        cards = content.split('---')
        for card in cards:
            if 'FRONT:' in card and 'BACK:' in card:
                lines = card.strip().split('\n')
                front = ""
                back = ""
                current_side = None
                
                for line in lines:
                    if line.startswith('FRONT:'):
                        current_side = 'front'
                        front = line.replace('FRONT:', '').strip()
                    elif line.startswith('BACK:'):
                        current_side = 'back'
                        back = line.replace('BACK:', '').strip()
                    elif current_side == 'front':
                        front += " " + line.strip()
                    elif current_side == 'back':
                        back += " " + line.strip()
                
                if front and back:
                    flashcards.append({
                        'front': front.strip(),
                        'back': back.strip()
                    })
        
        return flashcards[:count]  # Limit to requested count
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

def generate_flashcards_from_topic(topic, subject, difficulty, count=5):
    """Generate flashcards from a topic"""
    if not groq_client:
        return []
    
    prompt = f"""
    Create {count} educational flashcards about {topic} in {subject} at {difficulty} difficulty level.
    
    Format each flashcard as:
    FRONT: [Question or concept]
    BACK: [Answer or explanation]
    ---
    
    Make the flashcards comprehensive and educational.
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        flashcards = []
        
        # Parse flashcards (same parsing logic as above)
        cards = content.split('---')
        for card in cards:
            if 'FRONT:' in card and 'BACK:' in card:
                lines = card.strip().split('\n')
                front = ""
                back = ""
                current_side = None
                
                for line in lines:
                    if line.startswith('FRONT:'):
                        current_side = 'front'
                        front = line.replace('FRONT:', '').strip()
                    elif line.startswith('BACK:'):
                        current_side = 'back'
                        back = line.replace('BACK:', '').strip()
                    elif current_side == 'front':
                        front += " " + line.strip()
                    elif current_side == 'back':
                        back += " " + line.strip()
                
                if front and back:
                    flashcards.append({
                        'front': front.strip(),
                        'back': back.strip()
                    })
        
        return flashcards[:count]
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return []

# Authentication helpers
def is_logged_in():
    return 'user_id' in session and 'username' in session

def require_login(f):
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# HTML Templates
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #667eea;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .logo p {
            color: #666;
            font-size: 1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
        }
        .flash-messages {
            margin-bottom: 1rem;
        }
        .flash-message {
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .flash-error {
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        .flash-success {
            background: #efe;
            color: #393;
            border: 1px solid #cfc;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <h1>🤖 PhenBOT</h1>
            <p>Your AI Study Assistant</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <div class="links">
            <a href="{{ url_for('register') }}">Don't have an account? Sign up</a>
        </div>
    </div>
</body>
</html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT Register</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #667eea;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .logo p {
            color: #666;
            font-size: 1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
        }
        .flash-messages {
            margin-bottom: 1rem;
        }
        .flash-message {
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .flash-error {
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        .flash-success {
            background: #efe;
            color: #393;
            border: 1px solid #cfc;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <h1>🤖 PhenBOT</h1>
            <p>Create Your Account</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required minlength="3">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            <button type="submit" class="btn">Create Account</button>
        </form>
        
        <div class="links">
            <a href="{{ url_for('login') }}">Already have an account? Sign in</a>
        </div>
    </div>
</body>
</html>
'''
