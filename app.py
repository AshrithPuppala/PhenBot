from flask import Flask, request, jsonify, render_template
from groq import Groq
import os

app = Flask(__name__)

# Get Groq API key from environment variable (secure)
GROQ_API_KEY = os.getenv("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")

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

def ask_study_bot(question):
    if not groq_client:
        return "Study Bot unavailable. Missing API key."
    prompt = f"As an academic assistant, answer the following question: {question}"
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def api_ask():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'answer': 'Please enter a question.'})
    answer = ask_study_bot(question)
    return jsonify({'answer': answer})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)