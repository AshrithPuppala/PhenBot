from flask import Flask, request, jsonify, send_from_directory
import os
import sys

app = Flask(__name__, static_folder='static')

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    try:
        from groq import Groq
    except ImportError as e:
        GROQ_ERROR = "Groq library not installed"
        print(GROQ_ERROR, file=sys.stderr)
        return
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        GROQ_ERROR = "GROQ_API_KEY env variable missing"
        print(GROQ_ERROR, file=sys.stderr)
        return
    try:
        groq_client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("Groq client initialized successfully")
    except Exception as e:
        GROQ_ERROR = f"Groq initialization failed: {e}"
        print(GROQ_ERROR, file=sys.stderr)

initialize_groq()

@app.route('/')
def serve_index():
    # Serve your custom UI
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/ask', methods=['POST'])
def api_ask():
    if not GROQ_AVAILABLE:
        return jsonify({"error": f"Groq not available: {GROQ_ERROR}"}), 500
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': "Please enter a question."}), 400
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are PhenBOT, a helpful academic study companion."},
                {"role": "user", "content": question}
            ],
            model='llama-3.1-8b-instant',  # You can upgrade model here
            temperature=0.7,
            max_tokens=500
        )
        answer = response.choices[0].message.content
        return jsonify({'answer': answer})
    except Exception as e:
        print(f"Error from Groq API: {e}", file=sys.stderr)
        return jsonify({'error': f"Groq API error: {e}"}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
