<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhenBOT - Advanced Study Companion</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-bg: #0f0f23;
            --secondary-bg: #1a1a2e;
            --tertiary-bg: #16213e;
            --card-bg: rgba(30, 41, 59, 0.85);
            --card-border: rgba(71, 85, 105, 0.3);
            --primary-blue: #4f46e5;
            --primary-purple: #7c3aed;
            --primary-green: #10b981;
            --primary-cyan: #06b6d4;
            --primary-orange: #f59e0b;
            --primary-red: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #e2e8f0;
            --text-muted: #94a3b8;
            --text-disabled: #64748b;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 50%, var(--tertiary-bg) 100%);
            color: var(--text-secondary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        .app-container {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: 300px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--card-border);
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
            z-index: 100;
        }

        .sidebar-header {
            padding: 1.5rem;
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
            color: white;
        }

        .logo {
            display: flex;
            align-items: center;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .logo i {
            margin-right: 0.5rem;
            font-size: 1.8rem;
        }

        .tagline {
            font-size: 0.85rem;
            opacity: 0.9;
        }

        .sidebar-nav {
            flex: 1;
            padding: 1rem 0;
            overflow-y: auto;
        }

        .nav-item {
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            color: var(--text-muted);
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }

        .nav-item:hover, .nav-item.active {
            background: rgba(79, 70, 229, 0.1);
            color: var(--primary-blue);
            border-left-color: var(--primary-blue);
        }

        .nav-item i {
            width: 24px;
            margin-right: 0.75rem;
            font-size: 1.1rem;
        }

        .user-info {
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--card-border);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .user-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary-green), var(--primary-cyan));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
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
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--card-border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .top-bar-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .page-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(16, 185, 129, 0.2);
            color: var(--primary-green);
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .top-bar-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .pomodoro-mini {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(245, 158, 11, 0.2);
            color: var(--primary-orange);
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
        }

        .logout-btn {
            background: rgba(239, 68, 68, 0.2);
            color: var(--primary-red);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .logout-btn:hover {
            background: rgba(239, 68, 68, 0.3);
        }

        /* Content Area */
        .content-area {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* AI Chat Section */
        .ai-chat-container {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            height: calc(100vh - 200px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            padding: 1.5rem 2rem;
            background: linear-gradient(135deg, var(--primary-green), var(--primary-cyan));
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-title {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .chat-controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .mode-selector, .length-selector {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: white;
            font-size: 0.85rem;
            cursor: pointer;
        }

        .mode-selector option, .length-selector option {
            background: var(--secondary-bg);
            color: var(--text-secondary);
        }

        .voice-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }

        .voice-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .voice-btn.recording {
            background: var(--primary-red);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .chat-messages {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
            scroll-behavior: smooth;
        }

        .message {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            animation: slideIn 0.3s ease;
        }

        .message.user {
            flex-direction: row-reverse;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .message.user .message-avatar {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
            color: white;
        }

        .message.bot .message-avatar {
            background: linear-gradient(135deg, var(--primary-green), var(--primary-cyan));
            color: white;
        }

        .message-content {
            max-width: 70%;
            padding: 1rem 1.5rem;
            border-radius: 18px;
            line-height: 1.6;
            font-size: 0.95rem;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
            color: white;
            border-bottom-right-radius: 8px;
        }

        .message.bot .message-content {
            background: rgba(71, 85, 105, 0.3);
            color: var(--text-secondary);
            border-bottom-left-radius: 8px;
            border-left: 3px solid var(--primary-green);
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 1rem 1.5rem;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-muted);
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        .chat-input-area {
            padding: 1.5rem 2rem;
            border-top: 1px solid var(--card-border);
            background: rgba(15, 23, 42, 0.5);
        }

        .input-container {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }

        .chat-input {
            flex: 1;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--card-border);
            border-radius: 25px;
            padding: 1rem 1.5rem;
            color: var(--text-secondary);
            font-size: 0.95rem;
            resize: none;
            min-height: 50px;
            max-height: 120px;
            transition: all 0.3s ease;
        }

        .chat-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        .chat-input::placeholder {
            color: var(--text-disabled);
        }

        .send-btn {
            background: linear-gradient(135deg, var(--primary-green), var(--primary-cyan));
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }

        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
        }

        .send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* PDF Upload Section */
        .upload-container {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .upload-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .upload-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            margin-right: 1rem;
        }

        .upload-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .upload-area {
            border: 2px dashed var(--card-border);
            border-radius: 15px;
            padding: 3rem 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 1.5rem;
        }

        .upload-area:hover, .upload-area.dragover {
            border-color: var(--primary-blue);
            background: rgba(79, 70, 229, 0.05);
        }

        .upload-area i {
            font-size: 3rem;
            color: var(--primary-blue);
            margin-bottom: 1rem;
            display: block;
        }

        .file-input {
            display: none;
        }

        .pdf-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1rem;
        }

        .action-btn {
            background: linear-gradient(135deg, var(--primary-blue), var(--primary-purple));
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
        }

        .action-btn.secondary {
            background: linear-gradient(135deg, var(--primary-green), var(--primary-cyan));
        }

        .uploaded-files {
            margin-top: 1.5rem;
        }

        .file-item {
            background: rgba(15, 23, 42, 0.8);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .file-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .file-info i {
            color: var(--primary-red);
            font-size: 1.5rem;
        }

        .file-details h4 {
            color: var(--text-primary);
            font-size: 0.95rem;
            margin-bottom: 0.25rem;
        }

        .file-details p {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .file-actions {
            display: flex;
            gap: 0.5rem;
        }

        .icon-btn {
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }

        .icon-btn.primary {
            background: rgba(79, 70, 229, 0.2);
            color: var(--primary-blue);
        }

        .icon-btn.success {
            background: rgba(16, 185, 129, 0.2);
            color: var(--primary-green);
        }

        .icon-btn.danger {
            background: rgba(239, 68, 68, 0.2);
            color: var(--primary-red);
        }

        .icon-btn:hover {
            transform: translateY(-1px);
        }

        /* Flashcards Section */
        .flashcards-container {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 2rem;
        }

        .flashcard-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }

        .flashcard-nav {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .flashcard {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.1), rgba(124, 58, 237, 0.1));
            border: 1px solid var(--card-border);
            border-radius: 20px;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            perspective: 1000px;
            margin-bottom: 2rem;
        }

        .flashcard-inner {
            width: 100%;
            height: 100%;
            position: relative;
            transform-style: preserve-3d;
            transition: transform 0.3s ease;
            border-radius: 20px;
        }

        .flashcard.flipped .flashcard-inner {
            transform: rotateY(180deg);
        }

        .flashcard-front, .flashcard-back {
            position: absolute;
            width: 100%;
            height: 100%;
            backface-visibility: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            border-radius: 20px;
        }

        .flashcard-back {
            transform: rotateY(180deg);
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
        }

        .flashcard-content {
            font-size: 1.1rem;
            line-height: 1.6;
            color: var(--text-secondary);
        }

        /* Pomodoro Timer */
        .pomodoro-container {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
        }

        .timer-display {
            font-size: 4rem;
            font-weight: 700;
            color: var(--primary-orange);
            margin: 2rem 0;
            text-shadow: 0 0 30px rgba(245, 158, 11, 0.3);
        }

        .timer-controls {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .timer-btn {
            background: rgba(71, 85, 105, 0.3);
            color: var(--text-secondary);
            border: 1px solid var(--card-border);
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .timer-btn:hover {
            background: rgba(71, 85, 105, 0.5);
            transform: translateY(-2px);
        }

        .timer-btn.primary {
            background: linear-gradient(135deg, var(--primary-green), var(--primary-cyan));
            color: white;
            border-color: var(--primary-green);
        }

        .timer-settings {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
        }

        .setting-item {
            text-align: center;
        }

        .setting-item label {
            display: block;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }

        .setting-input {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 0.5rem;
            color: var(--text-secondary);
            width: 80px;
            text-align: center;
        }

        /* Responsive Design */
        @media (max-width: 1024px) {
            .sidebar {
                position: fixed;
                left: -300px;
                height: 100vh;
                z-index: 1000;
            }

            .sidebar.open {
                left: 0;
            }

            .main-content {
                width: 100%;
            }

            .sidebar-toggle {
                display: block;
                background: none;
                border: none;
                color: var(--text-secondary);
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0.5rem;
            }
        }

        @media (max-width: 768px) {
            .content-area {
                padding: 1rem;
            }

            .chat-controls {
                flex-direction: column;
                gap: 0.5rem;
            }

            .mode-selector, .length-selector {
                width: 100%;
            }

            .pdf-actions {
                flex-direction: column;
            }

            .flashcard-nav {
                flex-direction: column;
                gap: 0.5rem;
            }

            .timer-settings {
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    PhenBOT
                </div>
                <div class="tagline">Advanced Study Companion</div>
            </div>

            <nav class="sidebar-nav">
                <div class="nav-item active" data-tab="ai-chat">
                    <i class="fas fa-comments"></i>
                    AI Chat Assistant
                </div>
                <div class="nav-item" data-tab="pdf-tools">
                    <i class="fas fa-file-pdf"></i>
                    PDF Tools
                </div>
                <div class="nav-item" data-tab="flashcards">
                    <i class="fas fa-layer-group"></i>
                    Flashcards
                </div>
                <div class="nav-item" data-tab="pomodoro">
                    <i class="fas fa-clock"></i>
                    Pomodoro Timer
                </div>
                <div class="nav-item" data-tab="analytics">
                    <i class="fas fa-chart-line"></i>
                    Analytics
                </div>
                <div class="nav-item" data-tab="settings">
                    <i class="fas fa-cog"></i>
                    Settings
                </div>
            </nav>

            <div class="user-info">
                <div class="user-avatar">
                    {{ username[0].upper() if username else 'A' }}
                </div>
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">{{ username or 'ashrith07' }}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Premium User</div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Top Bar -->
            <div class="top-bar">
                <div class="top-bar-left">
                    <button class="sidebar-toggle" id="sidebarToggle" style="display: none;">
                        <i class="fas fa-bars"></i>
                    </button>
                    <div class="page-title" id="pageTitle">AI Chat Assistant</div>
                    <div class="status-badge">
                        <i class="fas fa-circle"></i>
                        <span id="aiStatus">AI Online</span>
                    </div>
                </div>
                <div class="top-bar-right">
                    <div class="pomodoro-mini" id="pomodoroMini">
                        <i class="fas fa-clock"></i>
                        <span id="miniTimer">25:00</span>
                    </div>
                    <button class="logout-btn" onclick="logout()">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </button>
                </div>
            </div>

            <!-- Content Area -->
            <div class="content-area">
                <!-- AI Chat Tab -->
                <div class="tab-content active" id="ai-chat">
                    <div class="ai-chat-container">
                        <div class="chat-header">
                            <div class="chat-title">AI Study Assistant</div>
                            <div class="chat-controls">
                                <select class="mode-selector" id="chatMode">
                                    <option value="normal">Normal Chat</option>
                                    <option value="analogy">Analogy Mode</option>
                                    <option value="quiz">Quiz Mode</option>
                                    <option value="teach">Teaching Mode</option>
                                    <option value="socratic">Socratic Method</option>
                                    <option value="explain">ELI5 Mode</option>
                                </select>
                                <select class="length-selector" id="responseLength">
                                    <option value="short">Short</option>
                                    <option value="normal">Normal</option>
                                    <option value="detailed">Detailed</option>
                                </select>
                                <button class="voice-btn" id="voiceBtn" title="Voice Chat">
                                    <i class="fas fa-microphone"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="chat-messages" id="chatMessages">
                            <div class="message bot">
                                <div class="message-avatar">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="message-content">
                                    Hello! I'm PhenBOT, your advanced study companion. I can help you in different modes:
                                    <br><br>
                                    📚 <strong>Normal:</strong> Regular conversation and help<br>
                                    🎭 <strong>Analogy:</strong> Explain concepts using analogies<br>
                                    ❓ <strong>Quiz:</strong> Test your knowledge<br>
                                    🎓 <strong>Teaching:</strong> Step-by-step explanations<br>
                                    🤔 <strong>Socratic:</strong> Learn through questioning<br>
                                    🌟 <strong>ELI5:</strong> Simple explanations<br><br>
                                    What would you like to learn today?
                                </div>
                            </div>
                        </div>
                        
                        <div class="chat-input-area">
                            <div class="input-container">
                                <textarea class="chat-input" id="chatInput" placeholder="Ask me anything..." rows="1"></textarea>
                                <button class="send-btn" id="sendBtn">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
