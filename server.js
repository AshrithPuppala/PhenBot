// server.js 
require("dotenv").config(); 
const http = require('http'); 
const url = require('url'); 
const fs = require('fs'); 
const path = require('path'); 
const https = require('https'); 
const formidable = require('formidable'); 
const pdfParse = require('pdf-parse'); 
const crypto = require('crypto'); 
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
// Create directories 
if (!fs.existsSync(USERS_DIR)) { 
fs.mkdirSync(USERS_DIR, { recursive: true }); 
console.log("📁 Created users directory"); 
} 
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
function saveSessions() { 
try { 
fs.writeFileSync(SESSIONS_FILE, JSON.stringify(activeSessions, null, 2)); 
} catch (error) { 
console.error("❌ Failed to save sessions:", error.message); 
} 
} 
// Hash password 
function hashPassword(password) { 
return crypto.createHash('sha256').update(password).digest('hex'); 
} 
// Generate session token 
function generateSessionToken() { 
return crypto.randomBytes(32).toString('hex'); 
} 
// Create user directory structure 
function createUserDirectories(userId) { 
const userDir = path.join(USERS_DIR, userId); 
const subDirs = ['pdfs', 'data', 'bookmarks', 'streaks', 'analytics', 'subjects']; 
[userDir, ...subDirs.map(dir => path.join(userDir, dir))].forEach(dir => { 
if (!fs.existsSync(dir)) { 
fs.mkdirSync(dir, { recursive: true }); 
} 
}); 
return userDir; 
} 
// User registration 
function registerUser(email, password, username) { 
const userId = crypto.createHash('md5').update(email).digest('hex'); 
const userFile = path.join(USERS_DIR, userId, 'profile.json'); 
if (fs.existsSync(userFile)) { 
return { success: false, error: 'User already exists' }; 
} 
createUserDirectories(userId); 
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
focusLevel: 'medium' 
}, 
analytics: { 
questionsAsked: 0, 
conceptsLearned: [], 
weakAreas: [], 
studyTime: 0 
} 
}; 
try { 
fs.writeFileSync(userFile, JSON.stringify(userData, null, 2)); 
console.log(`✅ User registered: ${email} (${userId})`); 
return { success: true, userId, username }; 
} catch (error) { 
return { success: false, error: 'Failed to create user' }; 
} 
} 
// User login 
function loginUser(email, password) { 
const userId = crypto.createHash('md5').update(email).digest('hex'); 
const userFile = path.join(USERS_DIR, userId, 'profile.json'); 
if (!fs.existsSync(userFile)) { 
return { success: false, error: 'User not found' }; 
} 
try { 
const userData = JSON.parse(fs.readFileSync(userFile, 'utf8')); 
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
fs.writeFileSync(userFile, JSON.stringify(userData, null, 2)); 
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
} catch (error) { 
return { success: false, error: 'Login failed' }; 
} 
} 
// Validate session 
function validateSession(sessionToken) { 
return activeSessions[sessionToken] || null; 
} 
// Get user data 
function getUserData(userId) { 
const userFile = path.join(USERS_DIR, userId, 'profile.json'); 
try { 
if (fs.existsSync(userFile)) { 
return JSON.parse(fs.readFileSync(userFile, 'utf8')); 
} 
} catch (error) { 
console.warn(`⚠️ Failed to load user data for ${userId}:`, error.message); 
} 
return null; 
} 
// Update user data 
function updateUserData(userId, updates) { 
const userFile = path.join(USERS_DIR, userId, 'profile.json'); 
try { 
const userData = getUserData(userId); 
if (userData) { 
Object.assign(userData, updates); 
fs.writeFileSync(userFile, JSON.stringify(userData, null, 2)); 
return true; 
} 
} catch (error) { 
console.error(`❌ Failed to update user data for ${userId}:`, error.message); 
} 
return false; 
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
// Enhanced Groq API query with personalization 
function queryGroq(question, userPreferences, pdfContext = null, mode = 'normal') { 
return new Promise((resolve, reject) => { 
if (!GROQ_API_KEY) return reject(new Error("Groq API key missing")); 
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
if (userPreferences.analogyStyle !== 'none') { 
systemPrompt += ` Use ${userPreferences.analogyStyle} analogies to explain complex concepts.`; 
} 
// Add Bloom's taxonomy level 
systemPrompt += ` Focus on ${userPreferences.bloomsLevel} level understanding.`; 
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
if (pdfContext) { 
prompt = `Use this reference material: ${pdfContext.text.substring(0, 2000)}\n\nQuestion: ${question}`; 
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
function calculateAccuracyScore(answer, confidence, source) { 
let score = confidence || 50; 
if (source === 'dataset') score += 30; 
if (source.includes('PDF')) score += 20; 
if (answer.length > 100) score += 10; 
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
const userData = userId ? getUserData(userId) : null; 
// --- Enhanced question handling --- 
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
// Get user's PDF context for the subject 
const pdfContext = null; // TODO: Implement subject-specific PDF storage 
// Analyze Bloom's level 
const bloomsLevel = analyzeBloomsLevel(trimmedQuestion); 
// First check dataset 
const datasetAnswer = dataset[subject]?.[trimmedQuestion] || null; 
let confidence = datasetAnswer ? 90 : 0; 
let answer, source; 
if (datasetAnswer && confidence > 70) { 
answer = datasetAnswer; 
source = "Local Dataset"; 
} else { 
try { 
answer = await queryGroq(trimmedQuestion, { ...(userData?.preferences || {}), difficulty }, pdfContext, mode); 
confidence = calculateAccuracyScore(answer, 75, source); 
source = pdfContext ? "AI + PDF Reference" : "AI Assistant"; 
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
if (!userData.analytics.conceptsLearned.includes(subject)) { 
userData.analytics.conceptsLearned.push(subject); 
} 
updateUserData(userId, userData); 
} 
res.end(JSON.stringify({ 
answer, 
confidence, 
source, 
bloomsLevel, 
accuracyScore: calculateAccuracyScore(answer, confidence, source), 
question: trimmedQuestion, 
mode, 
subject: subject || 'general' 
})); 
} catch (parseErr) { 
res.writeHead(400, {'Content-Type': 'application/json'}); 
res.end(JSON.stringify({ error: "Invalid request format", confidence: 0 })); 
} 
}); 
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
updateUserData(userId, userData); 
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
</style> 
</head> 
<body> 

