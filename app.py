from flask import Flask, request, jsonify, render_template
from groq import Groq
import os

app = Flask(__name__)

# Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route("/")
def index():
    return render_template("index.html")   # Flask auto-looks in /templates

@app.route("/api/ask", methods=["POST"])
def api_ask():
    if not groq_client:
        return jsonify({"error": "Groq not configured"}), 500

    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"answer": "Please enter a question."})

    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": question}],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=500
    )
    answer = response.choices[0].message.content
    return jsonify({"answer": answer})

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "groq_configured": groq_client is not None
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
