from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import instaloader
import os
import tempfile
import re

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://yashdeep04.github.io"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

def download_from_youtube(url):
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Download YouTube video
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        
        if not stream:
            raise Exception("No suitable video stream found")
            
        # Download to temporary file
        video_path = stream.download(output_path=temp_dir)
        return video_path
        
    except Exception as e:
        raise Exception(f"YouTube download failed: {str(e)}")

def download_from_instagram(url):
    try:
        L = instaloader.Instaloader()
        
        # Extract shortcode from URL
        if '/p/' in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        elif '/reel/' in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        else:
            raise Exception("Invalid Instagram URL")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Download post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if not post.is_video:
            raise Exception("This Instagram post does not contain a video")
            
        video_path = os.path.join(temp_dir, f"{shortcode}.mp4")
        L.download_post(post, target=temp_dir)
        
        # Find the downloaded video file
        for file in os.listdir(temp_dir):
            if file.endswith('.mp4'):
                return os.path.join(temp_dir, file)
        
        raise Exception("No video found in Instagram post")
        
    except Exception as e:
        raise Exception(f"Instagram download failed: {str(e)}")

@app.route('/')
def home():
    return "Video Downloader API is running!"

@app.route('/download', methods=['POST', 'OPTIONS'])
def download_video():
    if request.method == 'OPTIONS':
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
        
        if 'youtube.com' in url or 'youtu.be' in url:
            video_path = download_from_youtube(url)
        elif 'instagram.com' in url:
            video_path = download_from_instagram(url)
        else:
            return jsonify({'error': 'Unsupported URL. Only YouTube and Instagram are supported.'}), 400
        
        try:
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4'
            )
        except Exception as e:
            return jsonify({'error': f'Error sending file: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
