from flask import Flask, request, jsonify, render_template_string
import os
import sys

app = Flask(__name__)

# Print all environment variables for debugging
print("=== ENVIRONMENT VARIABLES ===")
for key, value in os.environ.items():
    if 'GROQ' in key or 'API' in key:
        print(f"{key}: {value[:10]}..." if value else f"{key}: (empty)")

# Try to import requests first (simpler test)
try:
    import requests
    print("✅ Requests library available")
except ImportError:
    print("❌ Requests library not available")

# Try to import groq
GROQ_AVAILABLE = False
GROQ_ERROR = None
groq_client = None

try:
    print("Testing groq import...")
    import groq
    print(f"✅ Groq imported successfully")
    
    from groq import Groq
    print("✅ Groq class imported")
    
    # Check for API key
    api_key = os.environ.get('GROQ_API_KEY')
    if api_key:
        print(f"✅ API key found: {api_key[:10]}...")
        groq_client = Groq(api_key=api_key)
        print("✅ Groq client created")
        GROQ_AVAILABLE = True
    else:
        print("❌ No API key found")
        GROQ_ERROR = "No API key found"
        
except Exception as e:
    print(f"❌ Groq error: {str(e)}")
    GROQ_ERROR = str(e)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PhenBOT Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .warning { background: #fff3cd; color: #856404; }
        .debug { background: #f8f9fa; padding: 15px; margin: 10px 0; font-family: monospace; font-size: 12px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        button:disabled { background: #6c757d; }
        input { padding: 10px; width: 70%; border: 1px solid #ddd; border-radius: 5px; }
        #messages { height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🤖 PhenBOT Test</h2>
        <div id="status" class="status">Loading...</div>
        <div id="debug" class="debug"></div>
        
        <div id="messages"></div>
        
        <input type="text" id="question" placeholder="Test question..." />
        <button id="send" onclick="testAPI()" disabled>Test</button>
        
        <h3>Manual Tests:</h3>
        <button onclick="testHealth()">Test Health Endpoint</button>
        <button onclick="testEnvVars()">Show Environment</button>
    </div>

    <script>
        async function checkStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                const debugDiv = document.getElementById('debug');
                
                if (data.groq_available && data.api_key_present) {
                    statusDiv.textContent = '✅ All systems working!';
                    statusDiv.className = 'status success';
                    document.getElementById('send').disabled = false;
                } else {
                    statusDiv.textContent = '❌ System issues detected';
                    statusDiv.className = 'status error';
                }
                
                debugDiv.innerHTML = `
                    <strong>System Status:</strong><br>
                    Python: ${data.python_version}<br>
                    Groq Available: ${data.groq_available}<br>
                    API Key Present: ${data.api_key_present}<br>
                    Error: ${data.error || 'None'}<br>
                    Environment Keys: ${data.env_sample}
                `;
                
            } catch (error) {
                document.getElementById('status').textContent = '❌ Connection failed';
                document.getElementById('status').className = 'status error';
            }
        }
        
        async function testAPI() {
            const question = document.getElementById('question').value;
            if (!question) return;
            
            const messages = document.getElementById('messages');
            messages.innerHTML += `<div><strong>You:</strong> ${question}</div>`;
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question})
                });
                const data = await response.json();
                messages.innerHTML += `<div><strong>Bot:</strong> ${data.answer || data.error}</div>`;
            } catch (error) {
                messages.innerHTML += `<div><strong>Error:</strong> ${error.message}</div>`;
            }
            
            messages.scrollTop = messages.scrollHeight;
            document.getElementById('question').value = '';
        }
        
        async function testHealth() {
            const response = await fetch('/health');
            const data = await response.json();
            alert(JSON.stringify(data, null, 2));
        }
        
        async function testEnvVars() {
            const response = await fetch('/env');
            const data = await response.json();
            alert(JSON.stringify(data, null, 2));
        }
        
        window.onload = checkStatus;
        
        document.getElementById('question').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') testAPI();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    api_key = os.environ.get('GROQ_API_KEY')
    return jsonify({
        'groq_available': GROQ_AVAILABLE,
        'api_key_present': bool(api_key),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'error': GROQ_ERROR,
        'env_sample': list(os.environ.keys())[:5]  # First 5 env vars
    })

@app.route('/env')
def env_info():
    # Return environment info for debugging
    return jsonify({
        'environment_variables': {k: v[:10] + "..." if len(v) > 10 else v 
                                for k, v in os.environ.items() 
                                if any(keyword in k.upper() for keyword in ['GROQ', 'API', 'KEY', 'RAILWAY'])},
        'working_directory': os.getcwd(),
        'python_path': sys.path[:3]
    })

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        if not GROQ_AVAILABLE:
            return jsonify({'error': f'Groq not available: {GROQ_ERROR}'})
        
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'})

        # Make a simple API call
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Answer briefly: {question}"}],
            model="llama-3.1-8b-instant",
            max_tokens=200
        )
        
        return jsonify({'answer': response.choices[0].message.content})
        
    except Exception as e:
        return jsonify({'error': f'API error: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting test app on port {port}")
    app.run(host='0.0.0.0', port=port)
