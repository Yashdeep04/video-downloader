from flask import Flask, request, send_file, jsonify
from flask_cors import CORS  # Import CORS
import requests
from io import BytesIO

app = Flask(__name__)
CORS(app)  # Enable CORS for the entire application

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Detect platform and download video
        if 'instagram.com' in url:
            video_content = download_from_instagram(url)
        elif 'facebook.com' in url:
            video_content = download_from_facebook(url)
        elif 'twitter.com' in url:
            video_content = download_from_twitter(url)
        elif 'tiktok.com' in url:
            video_content = download_from_tiktok(url)
        else:
            return jsonify({'error': 'Unsupported URL'}), 400

        return send_file(BytesIO(video_content), mimetype='video/mp4', as_attachment=True, attachment_filename='video.mp4')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_from_instagram(url):
    # Implement Instagram video download logic
    response = requests.get(url)
    return response.content

def download_from_facebook(url):
    # Implement Facebook video download logic
    response = requests.get(url)
    return response.content

def download_from_twitter(url):
    # Implement Twitter video download logic
    response = requests.get(url)
    return response.content

def download_from_tiktok(url):
    # Implement TikTok video download logic
    response = requests.get(url)
    return response.content

if __name__ == '__main__':
    app.run(debug=True)
