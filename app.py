from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import instaloader
import os
import tempfile
import re

app = Flask(__name__)
# Updated CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": ["https://yashdeep04.github.io"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Rest of your existing functions here...

@app.route('/download', methods=['POST', 'OPTIONS'])
def download_video():
    if request.method == 'OPTIONS':
        # Explicitly return response for OPTIONS request
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', 'https://yashdeep04.github.io')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({'error': 'Empty URL provided'}), 400
        
        # Your existing download logic here...
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
