# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, uuid
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)  # optional if frontend is separate

# ---------------------------
# Mock Auth
# ---------------------------
@app.route('/api/me')
def me():
    # Mock user
    return jsonify({"username": "Ashrith"}), 200

# ---------------------------
# Health
# ---------------------------
@app.route('/health')
def health():
    return jsonify({
        "groq_available": True,
        "api_key_present": True
    })

# ---------------------------
# Chat
# ---------------------------
history = []

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    subject = data.get('subject', 'general')
    answer = f"This is a mocked answer for: {question} (subject: {subject})"
    # save to history
    hist_entry = {
        "id": str(uuid.uuid4()),
        "subject": subject,
        "question": question,
        "answer": answer,
        "created_at": datetime.utcnow().isoformat()
    }
    history.insert(0, hist_entry)
    return jsonify({"answer": answer})

# ---------------------------
# History
# ---------------------------
@app.route('/api/history')
def get_history():
    return jsonify({"history": history})

# ---------------------------
# PDFs
# ---------------------------
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
pdf_files = []

@app.route('/api/pdfs')
def list_pdfs():
    files = [{"name": f["name"], "url": f"/uploads/{f['filename']}"} for f in pdf_files]
    return jsonify({"files": files})

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    pdf_files.append({"name": file.filename, "filename": filename})
    return jsonify({"message": "Uploaded"}), 201

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------------------------
# Flashcards
# ---------------------------
flashcards = []

@app.route('/api/flashcards', methods=['GET', 'POST'])
def handle_flashcards():
    if request.method == 'GET':
        return jsonify({"flashcards": flashcards})
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    if not question or not answer:
        return jsonify({"error": "Missing question/answer"}), 400
    fc = {"id": str(uuid.uuid4()), "question": question, "answer": answer}
    flashcards.insert(0, fc)
    return jsonify({"flashcard": fc}), 201

@app.route('/api/flashcards/<fc_id>', methods=['DELETE'])
def delete_flashcard(fc_id):
    global flashcards
    flashcards = [f for f in flashcards if f['id'] != fc_id]
    return '', 204

# ---------------------------
# Bookmarks
# ---------------------------
bookmarks = []

@app.route('/api/bookmarks', methods=['GET', 'POST'])
def handle_bookmarks():
    if request.method == 'GET':
        return jsonify({"bookmarks": bookmarks})
    data = request.json
    title = data.get('title')
    url = data.get('url')
    if not title or not url:
        return jsonify({"error": "Missing title/url"}), 400
    bm = {"id": str(uuid.uuid4()), "title": title, "url": url}
    bookmarks.insert(0, bm)
    return jsonify({"bookmark": bm}), 201

@app.route('/api/bookmarks/<bm_id>', methods=['DELETE'])
def delete_bookmark(bm_id):
    global bookmarks
    bookmarks = [b for b in bookmarks if b['id'] != bm_id]
    return '', 204

# ---------------------------
# Serve static SPA
# ---------------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
