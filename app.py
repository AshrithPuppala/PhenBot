from flask import Flask, request, jsonify, send_from_directory
import os
import sys

# Optional: if you installed groq client library
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False

app = Flask(__name__, static_folder="static")

groq_client = None
GROQ_ERROR = None

def initialize_groq():
    """Initialize the Groq client once with API key"""
    global groq_client, GROQ_ERROR
    if not GROQ_AVAILABLE:
        GROQ_ERROR = "Groq library not installed"
        return

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        GROQ_ERROR = "Missing GROQ_API_KEY env variable"
        return

    try:
        groq_client = Groq(api_key=api_key)
    except Exception as e:
        GROQ_ERROR = str(e)

initialize_groq()

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/ask", methods=["POST"])
def ask():
    """Endpoint that frontend calls with { question }"""
    data = request.get_json(force=True)
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Missing question"}), 400

    if not groq_client:
        return jsonify({"error": GROQ_ERROR or "Groq not initialized"}), 500

    try:
        # Example: use Groq LLM (adjust model name if needed)
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # or llama3, gemma, etc.
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=300,
        )

        answer = chat_completion.choices[0].message["content"]
        return jsonify({"answer": answer, "sources": []})

    except Exception as e:
        return jsonify({"error": f"GROQ request failed: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

