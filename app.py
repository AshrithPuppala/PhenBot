import os
import uuid
import re
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import openai
import PyPDF2

# Basic config
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# OpenAI config: set OPENAI_API_KEY in env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not set. Put your API key in environment variable.")
openai.api_key = OPENAI_API_KEY
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change if you prefer another model

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_system_prompt(mode):
    prompts = {
        "normal": "You are a helpful study assistant. Answer clearly and concisely.",
        "analogy": "You are a creative teacher. Explain concepts primarily using analogies and metaphors targeted to students.",
        "quiz": "You are a quiz master. Ask short questions or answer briefly as if checking knowledge. If asked to generate questions, produce well-formatted quizzes.",
        "teach": "You are a patient tutor. Give step-by-step explanations and walk through examples as needed.",
        "socratic": "You are a Socratic teacher. Encourage critical thinking by asking guiding questions and letting user reason. Keep your responses as questions or prompts that lead to insight.",
        "explain": "Explain like I'm five: simplify concepts with short, easy-to-understand language and short examples."
    }
    return prompts.get(mode, prompts["normal"])

def length_to_max_tokens(length):
    # rough tokens mapping for response size control
    mapping = {
        "short": 100,
        "normal": 300,
        "detailed": 900
    }
    return mapping.get(length, 300)

@app.route("/")
def index():
    # supply a username placeholder to template (you likely have real auth in your app)
    username = os.getenv("APP_USERNAME", "ashrith07")
    return render_template("index.html", username=username)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    mode = data.get("mode", "normal")
    length = data.get("length", "normal")

    if not message:
        return jsonify({"error": "No message"}), 400

    system_prompt = get_system_prompt(mode)
    max_tokens = length_to_max_tokens(length)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    try:
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.25
        )
        reply = resp["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/process_pdf", methods=["POST"])
def api_process_pdf():
    # POST form-data: file (pdf), action (summarize|flashcards), optionally num_cards, difficulty, topic
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    action = request.form.get("action", "summarize")
    num_cards = int(request.form.get("num_cards", 10))
    difficulty = request.form.get("difficulty", "medium")
    topic = request.form.get("topic", "")

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    filename = secure_filename(file.filename)
    saved_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, saved_name)
    file.save(path)

    # Extract text from PDF (simple extraction)
    try:
        text = ""
        reader = PyPDF2.PdfReader(path)
        for p in reader.pages:
            page_text = p.extract_text()
            if page_text:
                text += page_text + "\n\n"
    except Exception as e:
        return jsonify({"error": f"Failed to read PDF: {str(e)}"}), 500

    if not text.strip():
        return jsonify({"error": "No text could be extracted from this PDF."}), 400

    # truncate to a safe length for the model (we keep a chunk; for production you'd chunk and chain)
    text_chunk = text[:4000]

    try:
        if action == "summarize":
            prompt = (
                "You are an expert educational assistant. Summarize the document below in a clear, "
                "structured way with: (1) 3-sentence overview, (2) bullet-point key ideas, (3) 1-paragraph 'why it matters'. "
                "Be concise and student-friendly.\n\nDocument:\n" + text_chunk
            )
            resp = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.2
            )
            summary = resp["choices"][0]["message"]["content"]
            return jsonify({"summary": summary})

        elif action == "flashcards":
            # ask OpenAI to return a JSON array of flashcards
            prompt = (
                f"Create {num_cards} concise flashcards from the text below. Each flashcard must be an object with keys "
                f"'question', 'answer', and 'difficulty'. Use short answers (1-3 sentences). Prefer important/core concepts. "
                f"Document (or prefix context):\n{text_chunk}\n\nTopic hint: {topic}\nDesired difficulty: {difficulty}\n\n"
                "Return only valid JSON array, e.g. [{\"question\":\"...\",\"answer\":\"...\",\"difficulty\":\"...\"}, ...]."
            )
            resp = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                          {"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            content = resp["choices"][0]["message"]["content"]

            # Try to extract JSON array from the response
            match = re.search(r"(\[.*\])", content, re.S)
            json_text = match.group(1) if match else content

            try:
                cards = json.loads(json_text)
                return jsonify({"flashcards": cards})
            except Exception:
                # fallback: return raw content for debugging
                return jsonify({"raw": content}), 200
        else:
            return jsonify({"error": "Unknown action"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve static fallback (optional)
@app.route("/static/<path:p>")
def static_files(p):
    return send_from_directory("static", p)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
