<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PhenBOT - Advanced Study Companion</title>
  <style>
    /* your full CSS as before (no changes needed) */
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
        <a href="#dashboard" class="nav-tab active" data-tab="dashboard"><span class="nav-tab-icon">📊</span>Dashboard</a>
        <a href="#math" class="nav-tab" data-tab="math"><span class="nav-tab-icon">🔢</span>Mathematics</a>
        <a href="#science" class="nav-tab" data-tab="science"><span class="nav-tab-icon">🔬</span>Science</a>
        <a href="#english" class="nav-tab" data-tab="english"><span class="nav-tab-icon">📚</span>English</a>
        <a href="#history" class="nav-tab" data-tab="history"><span class="nav-tab-icon">🏛️</span>History</a>
        <a href="#tools" class="nav-tab" data-tab="tools"><span class="nav-tab-icon">🛠️</span>Study Tools</a>
        <a href="#bookmarks" class="nav-tab" data-tab="bookmarks"><span class="nav-tab-icon">🔖</span>Bookmarks</a>
        <a href="#analytics" class="nav-tab" data-tab="analytics"><span class="nav-tab-icon">📈</span>Analytics</a>
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
                <div class="card-title">Bloom's Analysis</div>
                <div class="card-icon">🧠</div>
              </div>
              <div class="bloom-chart">Skills Analysis Chart</div>
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
        </div>

        <!-- Math Tab -->
        <div class="tab-content" id="math">
          <div class="chat-container">
            <div class="chat-messages" id="mathMessages">
              <div class="message bot">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                  Welcome to Mathematics! I'm here to help you understand concepts through analogies and step-by-step explanations.
                </div>
              </div>
            </div>
            <div class="chat-input-area">
              <div class="input-container">
                <textarea class="message-input" placeholder="Ask a math question..." data-subject="math"></textarea>
                <div class="input-tools">
                  <button class="input-tool">📁</button>
                  <button class="input-tool">🎤</button>
                  <button class="input-tool">✏️</button>
                </div>
                <button class="send-button">➤</button>
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
                <div class="message-content">
                  Ready to explore Science! I can explain complex concepts using real-world analogies.
                </div>
              </div>
            </div>
            <div class="chat-input-area">
              <div class="input-container">
                <textarea class="message-input" placeholder="Ask a science question..." data-subject="science"></textarea>
                <div class="input-tools">
                  <button class="input-tool">📁</button>
                  <button class="input-tool">🎤</button>
                  <button class="input-tool">📊</button>
                </div>
                <button class="send-button">➤</button>
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
                <div class="message-content">Let's dive into English & Literature!</div>
              </div>
            </div>
            <div class="chat-input-area">
              <div class="input-container">
                <textarea class="message-input" placeholder="Ask about English/Literature..." data-subject="english"></textarea>
                <div class="input-tools">
                  <button class="input-tool">📁</button>
                  <button class="input-tool">🎤</button>
                  <button class="input-tool">✓</button>
                </div>
                <button class="send-button">➤</button>
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
                <div class="message-content">Welcome to History! I'll help with stories and timelines.</div>
              </div>
            </div>
            <div class="chat-input-area">
              <div class="input-container">
                <textarea class="message-input" placeholder="Ask a history question..." data-subject="history"></textarea>
                <div class="input-tools">
                  <button class="input-tool">📁</button>
                  <button class="input-tool">🎤</button>
                  <button class="input-tool">📅</button>
                </div>
                <button class="send-button">➤</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Tools Tab -->
        <div class="tab-content" id="tools">
          <h2>Study Tools & Resources</h2>
          <div class="file-upload"><div class="file-upload-icon">📄</div><h3>Upload Syllabus</h3></div>
        </div>

        <!-- Bookmarks Tab -->
        <div class="tab-content" id="bookmarks">
          <h2>Saved Answers & Bookmarks</h2>
          <div id="bookmarksList">
            <div class="bookmark-item"><div class="bookmark-title">Quadratic Formula Explanation</div></div>
            <div class="bookmark-item"><div class="bookmark-title">Newton's Laws of Motion</div></div>
          </div>
        </div>

        <!-- Analytics Tab -->
        <div class="tab-content" id="analytics">
          <h2>Learning Analytics</h2>
          <div class="dashboard-grid">
            <div class="dashboard-card">
              <div class="card-header">
                <div class="card-title">Bloom's Taxonomy Analysis</div>
                <div class="card-icon">🧠</div>
              </div>
            </div>
          </div>
        </div>

      </div> <!-- content-area -->
    </div> <!-- main-content -->
  </div> <!-- app-container -->
</body>
</html>
