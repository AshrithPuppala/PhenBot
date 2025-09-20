require("dotenv").config();
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
const https = require('https');
const formidable = require('formidable'); // For file uploads
const pdfParse = require('pdf-parse'); // For extracting PDF text

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

// --- Utility: simple similarity check ---
function calculateSimilarity(str1, str2) {
  const words1 = str1.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  const words2 = str2.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  if (!words1.length || !words2.length) return 0;
  const intersection = words1.filter(word => words2.includes(word));
  const union = [...new Set([...words1, ...words2])];
  return intersection.length / union.length;
}

// --- Groq API query ---
function queryGroq(prompt) {
  return new Promise((resolve, reject) => {
    if (!GROQ_API_KEY) return reject(new Error("Groq API key missing"));

    const payload = JSON.stringify({
      model: MODEL_NAME,
      messages: [
        { role: "system", content: "You are PhenBOT, an AI study companion. Answer clearly and concisely." },
        { role: "user", content: prompt }
      ],
      max_tokens: 500,
      temperature: 0.7
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

// --- Dataset lookup ---
function findAnswerFromDataset(question) {
  if (!Object.keys(dataset).length) return null;
  let bestMatch = null, bestScore = 0;
  Object.entries(dataset).forEach(([subject, qa]) => {
    Object.entries(qa).forEach(([q, a]) => {
      const score = calculateSimilarity(question, q);
      if (score > bestScore) {
        bestMatch = {
          answer: a,
          confidence: Math.round(score * 100),
          subject,
          matched_question: q
        };
        bestScore = score;
      }
    });
  });
  return bestMatch;
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
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

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

    // Handle question
    if (method === 'POST' && pathName === '/ask') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', async () => {
        try {
          const { question } = JSON.parse(body);
          if (!question || typeof question !== 'string') {
            return res.end(JSON.stringify({ error: "Invalid question" }));
          }

          const trimmedQuestion = question.trim();

          // Dataset lookup
          const datasetAns = findAnswerFromDataset(trimmedQuestion);
          if (datasetAns && datasetAns.confidence > 70) {
            return res.end(JSON.stringify({ ...datasetAns, source: "dataset" }));
          }

          // Fallback to Groq API
          try {
            const apiAnswer = await queryGroq(trimmedQuestion);
            res.end(JSON.stringify({
              answer: apiAnswer,
              confidence: 50,
              source: "Groq API",
              question: trimmedQuestion
            }));
          } catch (err) {
            if (datasetAns) {
              res.end(JSON.stringify({ ...datasetAns, note: "Groq API unavailable" }));
            } else {
              res.end(JSON.stringify({ error: "Service unavailable", confidence: 0 }));
            }
          }

        } catch {
          res.end(JSON.stringify({ error: "Invalid request body", confidence: 0 }));
        }
      });
      return;
    }

    // --- PDF Upload Endpoint ---
    if (method === 'POST' && pathName === '/upload-pdf') {
      const form = new formidable.IncomingForm();
      form.parse(req, async (err, fields, files) => {
        if (err || !files.pdf) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: "PDF file required" }));
          return;
        }

        const filePath = files.pdf.filepath || files.pdf.path;
        try {
          const dataBuffer = fs.readFileSync(filePath);
          const pdfData = await pdfParse(dataBuffer);
          const text = pdfData.text || "";

          // Query Groq API with extracted text
          const apiAnswer = await queryGroq(text);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ answer: apiAnswer, source: "PDF via Groq API" }));
        } catch (error) {
          res.writeHead(500);
          res.end(JSON.stringify({ error: "Failed to process PDF" }));
        }
      });
      return;
    }

    res.writeHead(404);
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
    console.log(`🚀 PhenBOT running on http://localhost:${port}`);
  });
}

const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
createServer(PORT);
