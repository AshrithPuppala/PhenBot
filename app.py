from flask import Flask, request, jsonify, send_from_directory
from groq import Groq
import os

app = Flask(__name__, static_folder='static', static_url_path='')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/ask', methods=['POST'])
def api_ask():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'answer': 'Please enter a question.'})
    if not groq_client:
        return jsonify({'answer': 'API key missing or client not initialized.'})
    prompt = f"As an academic assistant, answer the following question: {question}"
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        return jsonify({'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'answer': f'Error from AI server: {e}'})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
