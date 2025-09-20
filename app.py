from flask import Flask, request, jsonify, render_template
import os
import sys

app = Flask(__name__)

groq_client = None
GROQ_AVAILABLE = False
GROQ_ERROR = None

def initialize_groq():
    """
    Initialize the Groq client safely.
    Ensures no 'proxies' error by requiring httpx<0.28.
    """
    global groq_client, GROQ_AVAILABLE, GROQ_ERROR
    try:
        from groq import Groq
    except ImportError:
        GROQ_ERROR = "Groq library not installed"
        print(GROQ_ERROR, file=sys.stderr)
        return
    api_key = os.environ.get("GROQ_API_KEY")
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

# Initialize once at startup
initialize_groq()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "groq_available": GROQ_AVAILABLE,
        "api_key_present": bool(os.environ.get("GROQ_API_KEY")),
        "groq_error": GROQ_ERROR,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "status": "healthy" if GROQ_AVAILABLE else "error",
    })

@app.route("/api/ask", methods=["POST"])
def ask():
    if not GROQ_AVAILABLE:
        return jsonify({"error": f"Groq not available: {GROQ_ERROR}"}), 500

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are PhenBOT, a helpful academic assistant."},
                {"role": "user", "content": question},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=500,
        )
        return jsonify({"answer": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": f"Groq API error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
