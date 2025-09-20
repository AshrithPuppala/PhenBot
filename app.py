from flask import Flask, request, jsonify, send_from_directory
import os
import sys

app = Flask(__name__, static_folder='static')

# Your Groq and API init code...

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# API route as before
@app.route('/api/ask', methods=['POST'])
def api_ask():
    # Your existing api_ask code calling groq_client...
    pass

# Add static route for any connected static resources if used
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
