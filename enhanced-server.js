// enhanced-server.js
require("dotenv").config();
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
const https = require('https');
const formidable = require('formidable');
const pdfParse = require('pdf-parse');
const crypto = require('crypto');

// Import database setup
const { initializeDatabase, createUserDirectories } = require('./setup-database');

// Initialize database on startup
initializeDatabase();

// --- Load dataset ---
let dataset = {};
try {
  dataset = JSON.parse(fs.readFileSync("qa.json", "utf-8"));
  console.log("✅ Dataset loaded successfully");
} catch (error) {
  console.error("❌ Failed to load qa.json:", error.message);
}

// --- API setup ---
const GROQ_API_KEY = process.env.GROQ_API_KEY || "YOUR_GROQ_API_KEY";
const MODEL_NAME = "llama-3.1-8b-instant";
console.log(GROQ_API_KEY && GROQ_API_KEY !== "YOUR_GROQ_API_KEY" 
  ? "✅ Groq API key loaded" 
  : "⚠️ API key missing!");

// --- User & Session Management ---
const USERS_DIR = path.join(__dirname, 'users');
const SESSIONS_FILE = path.join(__dirname, 'sessions.json');
let activeSessions = {};

// Load active sessions
try {
  if (fs.existsSync(SESSIONS_FILE)) {
    activeSessions = JSON.parse(fs.readFileSync(SESSIONS_FILE, 'utf8'));
    console.log("✅ Active sessions loaded");
  }
} catch (error) {
  console.warn("⚠️ Failed to load sessions:", error.message);
}

// Save sessions
// Replace the saveSessions() function with:
function saveSessions() {
  try {
    fs.writeFileSync(SESSIONS_FILE, JSON.stringify(activeSessions, null, 2));
    console.log('✅ Sessions saved successfully');
  } catch (error) {
    console.error("❌ Failed to save sessions:", error.message);
  }
}

// Add automatic session cleanup every 24 hours:
setInterval(() => {
  const now = new Date();
  Object.keys(activeSessions).forEach(token => {
    const session = activeSessions[token];
    const sessionAge = now - new Date(session.createdAt);
    if (sessionAge > 24 * 60 * 60 * 1000) { // 24 hours
      delete activeSessions[token];
    }
  });
  saveSessions();
}, 60 * 60 * 1000); // Check every hour

// Hash password
function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

// Generate session token
function generateSessionToken() {
  return crypto.randomBytes(32).toString('hex');
}

// --- Enhanced User Data Management ---

// Get user file path
function getUserFilePath(userId, filename) {
  return path.join(USERS_DIR, userId, filename);
}

// Load user data from specific file
function loadUserData(userId, filename) {
  const filePath = getUserFilePath(userId, filename);
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  } catch (error) {
    console.warn(`⚠️ Failed to load ${filename} for ${userId}:`, error.message);
  }
  return null;
}

// Save user data to specific file
// Replace saveUserData function:
function saveUserData(userId, filename, data) {
  const filePath = getUserFilePath(userId, filename);
  const tempPath = filePath + '.tmp';
  try {
    fs.writeFileSync(tempPath, JSON.stringify(data, null, 2));
    fs.renameSync(tempPath, filePath);
    return true;
  } catch (error) {
    console.error(`❌ Failed to save ${filename} for ${userId}:`, error.message);
    if (fs.existsSync(tempPath)) {
      fs.unlinkSync(tempPath);
    }
    return false;
  }
}

// Get user profile
function getUserProfile(userId) {
  return loadUserData(userId, 'profile.json');
}

// Update user profile
function updateUserProfile(userId, updates) {
  const profile = getUserProfile(userId);
  if (profile) {
    Object.assign(profile, updates);
    return saveUserData(userId, 'profile.json', profile);
  }
  return false;
}

// User registration
function registerUser(email, password, username) {
  const userId = crypto.createHash('md5').update(email).digest('hex');
  const userDir = createUserDirectories(userId);
  
  if (fs.existsSync(path.join(userDir, 'profile.json'))) {
    const existingProfile = getUserProfile(userId);
    if (existingProfile && existingProfile.email) {
      return { success: false, error: 'User already exists' };
    }
  }
  
  const userData = {
    userId,
    email,
    username,
    password: hashPassword(password),
    createdAt: new Date().toISOString(),
    lastLogin: null,
    preferences: {
      answerLength: 'medium',
      analogyStyle: 'general',
      bloomsLevel: 'analyze',
      studyStreak: 0,
      focusLevel: 'medium',
      theme: 'dark'
    },
    analytics: {
      questionsAsked: 0,
      conceptsLearned: [],
      weakAreas: [],
      studyTime: 0,
      bloomsLevels: {
        remember: 0,
        understand: 0,
        apply: 0,
        analyze: 0,
        evaluate: 0,
        create: 0
      }
    }
  };

customSubjects: [],
subjectProgress: {},
dailyStats: {
  questionsToday: 0,
  minutesToday: 0,
  lastActiveDate: new Date().toISOString().split('T')[0]
}
  
  try {
    saveUserData(userId, 'profile.json', userData);
    console.log(`✅ User registered: ${email} (${userId})`);
    return { success: true, userId, username };
  } catch (error) {
    return { success: false, error: 'Failed to create user' };
  }
}

// User login
function loginUser(email, password) {
  const userId = crypto.createHash('md5').update(email).digest('hex');
  const userData = getUserProfile(userId);
  
  if (!userData) {
    return { success: false, error: 'User not found' };
  }
  
  if (userData.password !== hashPassword(password)) {
    return { success: false, error: 'Invalid password' };
  }
  
  // Update last login and streak
  const lastLogin = userData.lastLogin ? new Date(userData.lastLogin) : null;
  const today = new Date();
  const daysDiff = lastLogin ? Math.floor((today - lastLogin) / (1000 * 60 * 60 * 24)) : 1;
  
  if (daysDiff === 1) {
    userData.preferences.studyStreak += 1;
  } else if (daysDiff > 1) {
    userData.preferences.studyStreak = 1;
  }
  
  userData.lastLogin = today.toISOString();
  updateUserProfile(userId, userData);
  
  const sessionToken = generateSessionToken();
  activeSessions[sessionToken] = {
    userId,
    email: userData.email,
    username: userData.username,
    createdAt: new Date().toISOString()
  };
  saveSessions();
  
  console.log(`✅ User logged in: ${email}`);
  return {
    success: true,
    sessionToken,
    username: userData.username,
    userId,
    preferences: userData.preferences,
    analytics: userData.analytics
  };
}

// Validate session
function validateSession(sessionToken) {
  return activeSessions[sessionToken] || null;
}

// --- PDF Management ---

// Process uploaded PDF
async function processPDF(userId, fileData) {
  try {
    const pdfId = crypto.randomUUID();
    const filename = `${pdfId}.pdf`;
    const pdfPath = path.join(USERS_DIR, userId, 'pdfs', filename);
    
    // Save PDF file
    fs.writeFileSync(pdfPath, fileData.buffer);
    
    // Extract text
    const pdfBuffer = fs.readFileSync(pdfPath);
    const pdfData = await pdfParse(pdfBuffer);
    
    // Save extracted text
    const textPath = path.join(USERS_DIR, userId, 'extracted-text', `${pdfId}.txt`);
    fs.writeFileSync(textPath, pdfData.text);
    
    // Process text into chunks (for better context retrieval)
    const chunks = createTextChunks(pdfData.text);
    
    // Auto-detect subject (simple keyword matching)
    const subject = detectSubject(pdfData.text);
    
    // Create PDF metadata
    const pdfMetadata = {
      id: pdfId,
      originalName: fileData.originalFilename,
      filename: filename,
      uploadedAt: new Date().toISOString(),
      size: fileData.size,
      pages: pdfData.numpages,
      subject: subject,
      keywords: extractKeywords(pdfData.text),
      chunks: chunks
    };
    
    // Load existing PDFs and add new one
    let userPDFs = loadUserData(userId, 'pdfs.json') || {};
    userPDFs[pdfId] = pdfMetadata;
    saveUserData(userId, 'pdfs.json', userPDFs);
    
    return { success: true, pdfId, metadata: pdfMetadata };
    
  } catch (error) {
    console.error('PDF processing error:', error);
    return { success: false, error: 'Failed to process PDF' };
  }
}

// Create text chunks for better context retrieval
function createTextChunks(text, chunkSize = 1000) {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const chunks = [];
  let currentChunk = '';
  let chunkId = 0;
  
  for (const sentence of sentences) {
    if ((currentChunk + sentence).length > chunkSize && currentChunk.length > 0) {
      chunks.push({
        id: `chunk-${chunkId++}`,
        text: currentChunk.trim(),
        length: currentChunk.length
      });
      currentChunk = sentence;
    } else {
      currentChunk += sentence + '. ';
    }
  }
  
  if (currentChunk.trim().length > 0) {
    chunks.push({
      id: `chunk-${chunkId}`,
      text: currentChunk.trim(),
      length: currentChunk.length
    });
  }
  
  return chunks;
}

// Detect subject from text content
function detectSubject(text) {
  const lowerText = text.toLowerCase();
  const subjects = {
    mathematics: ['equation', 'theorem', 'proof', 'calculus', 'algebra', 'geometry', 'derivative', 'integral'],
    physics: ['force', 'energy', 'momentum', 'velocity', 'acceleration', 'mass', 'gravity', 'quantum'],
    chemistry: ['molecule', 'atom', 'reaction', 'compound', 'element', 'periodic', 'bond', 'ion'],
    biology: ['cell', 'organism', 'gene', 'protein', 'evolution', 'species', 'dna', 'enzyme'],
    programming: ['function', 'variable', 'algorithm', 'code', 'programming', 'software', 'data structure'],
    history: ['war', 'empire', 'civilization', 'century', 'revolution', 'ancient', 'medieval'],
    literature: ['poem', 'novel', 'author', 'character', 'plot', 'theme', 'narrative']
  };
  
  let maxScore = 0;
  let detectedSubject = 'general';
  
  for (const [subject, keywords] of Object.entries(subjects)) {
    const score = keywords.reduce((acc, keyword) => {
      const matches = (lowerText.match(new RegExp(keyword, 'g')) || []).length;
      return acc + matches;
    }, 0);
    
    if (score > maxScore) {
      maxScore = score;
      detectedSubject = subject;
    }
  }
  
  return detectedSubject;
}

// Extract keywords from text
function extractKeywords(text, limit = 10) {
  const words = text.toLowerCase().match(/\b\w{4,}\b/g) || [];
  const frequency = {};
  
  words.forEach(word => {
    frequency[word] = (frequency[word] || 0) + 1;
  });
  
  return Object.entries(frequency)
    .sort(([,a], [,b]) => b - a)
    .slice(0, limit)
    .map(([word]) => word);
}

// Get relevant PDF context for a question
function getPDFContext(userId, question, maxChunks = 3) {
  const userPDFs = loadUserData(userId, 'pdfs.json') || {};
  const questionLower = question.toLowerCase();
  const relevantChunks = [];
  
  Object.values(userPDFs).forEach(pdf => {
    pdf.chunks.forEach(chunk => {
      // Simple relevance scoring based on keyword matching
      const chunkLower = chunk.text.toLowerCase();
      const commonWords = questionLower.split(/\s+/).filter(word => 
        word.length > 3 && chunkLower.includes(word)
      );
      
      if (commonWords.length > 0) {
        relevantChunks.push({
          text: chunk.text,
          score: commonWords.length,
          pdfName: pdf.originalName,
          pdfId: pdf.id
        });
      }
    });
  });
  
  // Sort by relevance score and return top chunks
  return relevantChunks
    .sort((a, b) => b.score - a.score)
    .slice(0, maxChunks);
}

// --- Flashcard Management ---

// Create user-made flashcard
function createUserFlashcard(userId, cardData) {
  const flashcards = loadUserData(userId, 'flashcards.json') || { userMade: [], aiGenerated: [] };
  
  const newCard = {
    id: crypto.randomUUID(),
    question: cardData.question,
    answer: cardData.answer,
    subject: cardData.subject || 'general',
    difficulty: cardData.difficulty || 5,
    createdAt: new Date().toISOString(),
    lastReviewed: null,
    reviewCount: 0,
    correctCount: 0,
    tags: cardData.tags || []
  };
  
  flashcards.userMade.push(newCard);
  saveUserData(userId, 'flashcards.json', flashcards);
  
  return { success: true, card: newCard };
}

// Generate AI flashcards from PDF content
async function generateAIFlashcards(userId, pdfId, count = 5) {
  const userPDFs = loadUserData(userId, 'pdfs.json') || {};
  const pdf = userPDFs[pdfId];
  
  if (!pdf) {
    return { success: false, error: 'PDF not found' };
  }
  
  const flashcards = loadUserData(userId, 'flashcards.json') || { userMade: [], aiGenerated: [] };
  const generatedCards = [];
  
  try {
    // Use PDF chunks to generate flashcards
    for (let i = 0; i < Math.min(count, pdf.chunks.length); i++) {
      const chunk = pdf.chunks[i];
      const prompt = `Based on this text, create a flashcard question and answer:

Text: ${chunk.text.substring(0, 500)}

Create a clear, educational question and concise answer. Format as:
Q: [question]
A: [answer]`;

      const response = await queryGroq(prompt, { answerLength: 'short' });
      
      if (response) {
        const lines = response.split('\n');
        const questionLine = lines.find(line => line.startsWith('Q:'));
        const answerLine = lines.find(line => line.startsWith('A:'));
        
        if (questionLine && answerLine) {
          const card = {
            id: crypto.randomUUID(),
            question: questionLine.substring(2).trim(),
            answer: answerLine.substring(2).trim(),
            subject: pdf.subject,
            difficulty: 5,
            createdAt: new Date().toISOString(),
            sourceDocument: pdfId,
            lastReviewed: null,
            reviewCount: 0,
            correctCount: 0,
            tags: ['ai-generated', pdf.subject]
          };
          
          flashcards.aiGenerated.push(card);
          generatedCards.push(card);
        }
      }
    }
    
    saveUserData(userId, 'flashcards.json', flashcards);
    return { success: true, cards: generatedCards };
    
  } catch (error) {
    console.error('AI flashcard generation error:', error);
    return { success: false, error: 'Failed to generate flashcards' };
  }
}

// --- Enhanced AI Functions ---

// Calculate similarity
function calculateSimilarity(str1, str2) {
  const words1 = str1.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  const words2 = str2.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  if (!words1.length || !words2.length) return 0;
  const intersection = words1.filter(word => words2.includes(word));
  const union = [...new Set([...words1, ...words2])];
  return intersection.length / union.length;
}

// Enhanced Groq API query with PDF context
function queryGroq(question, userPreferences = {}, pdfContext = null, mode = 'normal') {
  return new Promise((resolve, reject) => {
    if (!GROQ_API_KEY || GROQ_API_KEY === "YOUR_GROQ_API_KEY") {
      return reject(new Error("Groq API key missing"));
    }

    let maxTokens, temperature;
    let systemPrompt = "You are PhenBOT, an advanced AI study companion.";

    // Adjust based on user preferences
    switch(userPreferences.answerLength) {
      case 'short':
        maxTokens = 200;
        temperature = 0.3;
        systemPrompt += " Keep answers concise and to the point.";
        break;
      case 'long':
        maxTokens = 1000;
        temperature = 0.7;
        systemPrompt += " Provide comprehensive, detailed explanations with examples.";
        break;
      case 'medium':
      default:
        maxTokens = 500;
        temperature = 0.5;
        systemPrompt += " Provide clear, informative answers.";
    }

    // Add analogy-based learning
    if (userPreferences.analogyStyle && userPreferences.analogyStyle !== 'none') {
      systemPrompt += ` Use ${userPreferences.analogyStyle} analogies to explain complex concepts.`;
    }

    // Add Bloom's taxonomy level
    if (userPreferences.bloomsLevel) {
      systemPrompt += ` Focus on ${userPreferences.bloomsLevel} level understanding.`;
    }

    // Different modes
    switch(mode) {
      case 'reverse':
        systemPrompt += " Act as a student asking probing questions to test understanding.";
        break;
      case 'summary':
        systemPrompt += " Ask the user to summarize the concept in their own words after explaining.";
        break;
      case 'quiz':
        systemPrompt += " End with a quick quiz question related to the topic.";
        break;
    }

    let prompt = question;
    
    // Add PDF context if available
    if (pdfContext && pdfContext.length > 0) {
      const contextTexts = pdfContext.map(chunk => 
        `From "${chunk.pdfName}": ${chunk.text.substring(0, 800)}`
      ).join('\n\n');
      
      prompt = `Use this reference material to help answer the question:

${contextTexts}

Question: ${question}

Please provide a comprehensive answer using the reference material above.`;
    }

    const payload = JSON.stringify({
      model: MODEL_NAME,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: prompt }
      ],
      max_tokens: maxTokens,
      temperature: temperature
    });

    const options = {
      hostname: 'api.groq.com',
      port: 443,
      path: '/openai/v1/chat/completions',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = https.request(options, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          const answer = json.choices?.[0]?.message?.content?.trim();
          if (!answer) reject(new Error("No response from Groq"));
          else resolve(answer);
        } catch (err) {
          reject(new Error("Failed to parse Groq response: " + err.message));
        }
      });
    });

    req.on('error', err => reject(err));
    req.write(payload);
    req.end();
  });
}

// Calculate accuracy score
function calculateAccuracyScore(answer, confidence = 50, source = '', hasPDFContext = false) {
  let score = (typeof confidence === 'number') ? confidence : 50;
  if (String(source).toLowerCase().includes('dataset')) score += 30;
  if (String(source).toLowerCase().includes('pdf') || hasPDFContext) score += 25;
  if (answer && typeof answer === 'string' && answer.length > 100) score += 10;
  return Math.min(Math.max(score, 0), 100);
}

// Analyze Bloom's taxonomy level
function analyzeBloomsLevel(question) {
  const lowerQ = String(question).toLowerCase();
  const createKeywords = ["create","design","compose","develop","plan","construct","produce","formulate","invent","synthesize"];
  const evaluateKeywords = ["evaluate","judge","critique","assess","recommend","justify","argue","support","value","appraise"];
  const analyzeKeywords = ["analyze","compare","contrast","differentiate","examine","test","categorize","investigate","organize"];
  const applyKeywords = ["apply","demonstrate","use","execute","implement","solve","show","perform","experiment","illustrate"];
  const understandKeywords = ["explain","describe","summarize","paraphrase","interpret","classify","discuss","identify","report"];
  const rememberKeywords = ["define","list","recall","state","name","label","repeat","who","what","when","where"];
  
  if (createKeywords.some(kw => lowerQ.includes(kw))) return "create";
  if (evaluateKeywords.some(kw => lowerQ.includes(kw))) return "evaluate";
  if (analyzeKeywords.some(kw => lowerQ.includes(kw))) return "analyze";
  if (applyKeywords.some(kw => lowerQ.includes(kw))) return "apply";
  if (understandKeywords.some(kw => lowerQ.includes(kw))) return "understand";
  if (rememberKeywords.some(kw => lowerQ.includes(kw))) return "remember";
  return "understand";
}

// Save chat history
function saveChatHistory(userId, question, answer, metadata) {
  const chatHistory = loadUserData(userId, 'chat-history.json') || [];
  
  const chatEntry = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    question,
    answer,
    metadata
  };
  
  chatHistory.push(chatEntry);
  
  // Keep only last 100 conversations to manage storage
  if (chatHistory.length > 100) {
    chatHistory.splice(0, chatHistory.length - 100);
  }
  
  saveUserData(userId, 'chat-history.json', chatHistory);
}

// --- Server setup ---
function createServer(port) {
  const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const pathName = parsedUrl.pathname;
    const method = req.method;

    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

    // Serve frontend
    if (method === 'GET' && (pathName === '/' || pathName === '/index.html')) {
      const indexPath = path.join(__dirname, 'frontend.html');
      fs.readFile(indexPath, 'utf8', (err, data) => {
        if (err) { res.writeHead(500); res.end("Failed to load frontend"); return; }
        res.setHeader('Content-Type', 'text/html');
        res.writeHead(200);
        res.end(data);
      });
      return;
    }

    // --- Authentication endpoints ---
    if (method === 'POST' && pathName === '/register') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const { email, password, username } = JSON.parse(body);
          if (!email || !password || !username) {
            res.writeHead(400, {'Content-Type': 'application/json'});
            return res.end(JSON.stringify({ success: false, error: 'Missing required fields' }));
          }
          const result = registerUser(email, password, username);
          res.setHeader('Content-Type', 'application/json');
          res.writeHead(result.success ? 200 : 400);
          res.end(JSON.stringify(result));
        } catch (error) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ success: false, error: 'Invalid request' }));
        }
      });
      return;
    }

    if (method === 'POST' && pathName === '/login') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const { email, password } = JSON.parse(body);
          if (!email || !password) {
            res.writeHead(400, {'Content-Type': 'application/json'});
            return res.end(JSON.stringify({ success: false, error: 'Email and password required' }));
          }
          const result = loginUser(email, password);
          res.setHeader('Content-Type', 'application/json');
          res.writeHead(result.success ? 200 : 400);
          res.end(JSON.stringify(result));
        } catch (error) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ success: false, error: 'Invalid request' }));
        }
      });
      return;
    }

    // --- Protected endpoints ---
    // Logout endpoint
    if (method === 'POST' && pathName === '/logout') {
      const auth = req.headers.authorization;
      const token = auth ? auth.replace('Bearer ', '') : null;
      if (token && activeSessions[token]) {
        delete activeSessions[token];
        saveSessions();
      }
      res.writeHead(200, {'Content-Type':'application/json'});
      res.end(JSON.stringify({ success: true, message: 'Logged out successfully' }));
      return;
    }

    const authHeader = req.headers.authorization;
    const sessionToken = authHeader ? authHeader.replace('Bearer ', '') : null;
    const session = sessionToken ? validateSession(sessionToken) : null;
    if (!session && !pathName.startsWith('/public')) {
      res.writeHead(401, {'Content-Type': 'application/json'});
      return res.end(JSON.stringify({ error: 'Unauthorized' }));
    }

    const userId = session?.userId;
    const userData = userId ? getUserProfile(userId) : null;

    // --- Enhanced question handling with PDF context ---
    if (method === 'POST' && pathName === '/ask') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', async () => {
        try {
          const { question, mode = 'normal', subject, difficulty = 5 } = JSON.parse(body);
          if (!question || typeof question !== 'string') {
            res.writeHead(400, {'Content-Type': 'application/json'});
            return res.end(JSON.stringify({ error: "Invalid question" }));
          }
          const trimmedQuestion = question.trim();
          res.setHeader('Content-Type', 'application/json');

          // Get relevant PDF context
          const pdfContext = getPDFContext(userId, trimmedQuestion);
          const hasPDFContext = pdfContext.length > 0;

          // Analyze Bloom's level
          const bloomsLevel = analyzeBloomsLevel(trimmedQuestion);

          // First check dataset
          const datasetAnswer = dataset[subject]?.[trimmedQuestion] || null;
          let confidence = datasetAnswer ? 90 : 0;
          let answer, source;

          if (datasetAnswer && confidence > 70 && !hasPDFContext) {
            answer = datasetAnswer;
            source = "Local Dataset";
          } else {
            try {
              answer = await queryGroq(
                trimmedQuestion, 
                { ...(userData?.preferences || {}), difficulty }, 
                hasPDFContext ? pdfContext : null, 
                mode
              );
              source = hasPDFContext ? "AI + PDF Reference" : "AI Assistant";
              confidence = calculateAccuracyScore(answer, 75, source, hasPDFContext);
            } catch (err) {
              console.error("Groq API error:", err.message);
              if (datasetAnswer) {
                answer = datasetAnswer;
                source = "Local Dataset (AI unavailable)";
                confidence = 60;
              } else {
                res.end(JSON.stringify({
                  error: "Service temporarily unavailable. Please try again.",
                  confidence: 0,
                  source: "Error"
                }));
                return;
              }
            }
          }

          // Update user analytics
          if (userData) {
            userData.analytics.questionsAsked += 1;
            if (subject && !userData.analytics.conceptsLearned.includes(subject)) {
              userData.analytics.conceptsLearned.push(subject);
            }
            if (bloomsLevel) {
              userData.analytics.bloomsLevels[bloomsLevel] = 
                (userData.analytics.bloomsLevels[bloomsLevel] || 0) + 1;
            }
            updateUserProfile(userId, userData);
          }

          // Save chat history
          const metadata = {
            mode,
            subject: subject || 'general',
            source,
            accuracy: confidence,
            bloomsLevel,
            difficulty,
            pdfSources: pdfContext.map(ctx => ctx.pdfId)
          };
          
          if (userId) {
            saveChatHistory(userId, trimmedQuestion, answer, metadata);
          }

          res.end(JSON.stringify({
            answer,
            confidence,
            source,
            bloomsLevel,
            accuracyScore: calculateAccuracyScore(answer, confidence, source, hasPDFContext),
            question: trimmedQuestion,
            mode,
            subject: subject || 'general',
            pdfSources: pdfContext.map(ctx => ({ name: ctx.pdfName, id: ctx.pdfId }))
          }));
        } catch (parseErr) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ error: "Invalid request format", confidence: 0 }));
        }
      });
      return;
    }

    // --- PDF Upload endpoint ---
    if (method === 'POST' && pathName === '/upload-pdf') {
      const form = new formidable.IncomingForm();
      form.uploadDir = path.join(__dirname, 'temp');
      form.keepExtensions = true;
      
      form.parse(req, async (err, fields, files) => {
        if (err) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          return res.end(JSON.stringify({ success: false, error: 'Upload failed' }));
        }
        
        const file = files.pdf;
        if (!file) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          return res.end(JSON.stringify({ success: false, error: 'No PDF file uploaded' }));
        }
        
        try {
          const fileData = {
            buffer: fs.readFileSync(file.filepath),
            originalFilename: file.originalFilename,
            size: file.size
          };
          
          const result = await processPDF(userId, fileData);
          
          // Clean up temp file
          fs.unlinkSync(file.filepath);
          
          res.setHeader('Content-Type', 'application/json');
          res.writeHead(result.success ? 200 : 400);
          res.end(JSON.stringify(result));
        } catch (error) {
          console.error('PDF upload error:', error);
          res.writeHead(500, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ success: false, error: 'PDF processing failed' }));
        }
      });
      return;
    }

    // --- Multiple PDF Upload endpoint ---
if (method === 'POST' && pathName === '/upload-multiple-pdfs') {
  const form = new formidable.IncomingForm();
  form.multiples = true;
  form.uploadDir = path.join(__dirname, 'temp');
  
  form.parse(req, async (err, fields, files) => {
    if (err) {
      res.writeHead(400, {'Content-Type': 'application/json'});
      return res.end(JSON.stringify({ success: false, error: 'Upload failed' }));
    }
    
    const pdfFiles = Array.isArray(files.pdfs) ? files.pdfs : [files.pdfs].filter(Boolean);
    const results = [];
    
    for (const file of pdfFiles) {
      try {
        const fileData = {
          buffer: fs.readFileSync(file.filepath),
          originalFilename: file.originalFilename,
          size: file.size
        };
        const result = await processPDF(userId, fileData);
        results.push(result);
        fs.unlinkSync(file.filepath);
      } catch (error) {
        results.push({ success: false, error: `Failed to process ${file.originalFilename}` });
      }
    }
    
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ success: true, results }));
  });
  return;
}

    // --- Get user PDFs ---
    if (method === 'GET' && pathName === '/user-pdfs') {
      const userPDFs = loadUserData(userId, 'pdfs.json') || {};
      const pdfList = Object.values(userPDFs).map(pdf => ({
        id: pdf.id,
        originalName: pdf.originalName,
        uploadedAt: pdf.uploadedAt,
        subject: pdf.subject,
        pages: pdf.pages,
        keywords: pdf.keywords
      }));
      
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: true, pdfs: pdfList }));
      return;
    }

    // --- Flashcard endpoints ---
    if (method === 'POST' && pathName === '/create-flashcard') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const cardData = JSON.parse(body);
          const result = createUserFlashcard(userId, cardData);
          res.setHeader('Content-Type', 'application/json');
          res.writeHead(result.success ? 200 : 400);
          res.end(JSON.stringify(result));
        } catch (error) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ success: false, error: 'Invalid request' }));
        }
      });
      return;
    }

    if (method === 'POST' && pathName === '/generate-ai-flashcards') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', async () => {
        try {
          const { pdfId, count = 5 } = JSON.parse(body);
          const result = await generateAIFlashcards(userId, pdfId, count);
          res.setHeader('Content-Type', 'application/json');
          res.writeHead(result.success ? 200 : 400);
          res.end(JSON.stringify(result));
        } catch (error) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ success: false, error: 'Invalid request' }));
        }
      });
      return;
    }

    if (method === 'GET' && pathName === '/flashcards') {
      const flashcards = loadUserData(userId, 'flashcards.json') || { userMade: [], aiGenerated: [] };
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: true, flashcards }));
      return;
    }

    // --- User preferences ---
    if (method === 'POST' && pathName === '/preferences') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const preferences = JSON.parse(body);
          if (userData) {
            userData.preferences = { ...userData.preferences, ...preferences };
            updateUserProfile(userId, userData);
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ success: true }));
          } else {
            res.writeHead(404, {'Content-Type': 'application/json'});
            res.end(JSON.stringify({ error: 'User not found' }));
          }
        } catch (error) {
          res.writeHead(400, {'Content-Type': 'application/json'});
          res.end(JSON.stringify({ error: 'Invalid request' }));
        }
      });
      return;
    }

    // --- Get user analytics ---
    if (method === 'GET' && pathName === '/analytics') {
      res.setHeader('Content-Type', 'application/json');
      if (userData) {
        res.end(JSON.stringify(userData.analytics));
      } else {
        res.writeHead(404);
        res.end(JSON.stringify({ error: 'User not found' }));
      }
      return;
    }

    // --- Get chat history ---
    if (method === 'GET' && pathName === '/chat-history') {
      const chatHistory = loadUserData(userId, 'chat-history.json') || [];
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: true, history: chatHistory.slice(-20) })); // Last 20 conversations
      return;
    }

    // --- User subjects endpoints ---
if (method === 'GET' && pathName === '/user-subjects') {
  const profile = getUserProfile(userId);
  const subjects = profile?.customSubjects || [];
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify({ success: true, subjects }));
  return;
}

    if (method === 'POST' && pathName === '/add-subject') {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    try {
      const { subject } = JSON.parse(body);
      const profile = getUserProfile(userId);
      if (profile) {
        profile.customSubjects = profile.customSubjects || [];
        if (!profile.customSubjects.includes(subject)) {
          profile.customSubjects.push(subject);
          updateUserProfile(userId, profile);
        }
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ success: true }));
      }
    } catch (error) {
      res.writeHead(400, {'Content-Type': 'application/json'});
      res.end(JSON.stringify({ success: false, error: 'Invalid request' }));
    }
  });
  return;
}

    if (method === 'POST' && pathName === '/remove-subject') {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    try {
      const { subject } = JSON.parse(body);
      const profile = getUserProfile(userId);
      if (profile && profile.customSubjects) {
        profile.customSubjects = profile.customSubjects.filter(s => s !== subject);
        updateUserProfile(userId, profile);
      }
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: true }));
    } catch (error) {
      res.writeHead(400, {'Content-Type': 'application/json'});
      res.end(JSON.stringify({ success: false, error: 'Invalid request' }));
    }
  });
  return;
}

    // 404 handler
    res.writeHead(404, {'Content-Type': 'text/plain'});
    res.end("Not found");
  });

  server.on("error", err => {
    if (err.code === "EADDRINUSE") {
      console.warn(`⚠️ Port ${port} in use, trying ${port + 1}...`);
      createServer(port + 1);
    } else {
      console.error("Server error:", err);
    }
  });

  server.listen(port, () => {
    console.log(`🚀 Enhanced PhenBOT running on http://localhost:${port}`);
    console.log(`👥 Users directory: ${USERS_DIR}`);
    console.log(`📁 Database initialized with user-specific storage`);
  });
}

// Cleanup on exit
process.on('SIGINT', () => {
  saveSessions();
  console.log('\n💾 Sessions saved. Goodbye!');
  process.exit(0);
});

// Start server
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;

createServer(PORT);
