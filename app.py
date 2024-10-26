from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import instaloader
import os
import tempfile
from io import BytesIO

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/download', methods=['POST', 'OPTIONS'])
def download_video():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'CORS preflight'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response

    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        if 'youtube.com' in url or 'youtu.be' in url:
            video_path = download_from_youtube(url)
            return send_file(video_path, mimetype='video/mp4', as_attachment=True, 
                           attachment_filename='youtube_video.mp4')
        
        elif 'instagram.com' in url:
            video_path = download_from_instagram(url)
            return send_file(video_path, mimetype='video/mp4', as_attachment=True, 
                           attachment_filename='instagram_video.mp4')
        else:
            return jsonify({'error': 'Unsupported URL. Only YouTube and Instagram are supported.'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_from_youtube(url):
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Download YouTube video
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable video stream found")
            
        # Download to temporary file
        video_path = stream.download(output_path=temp_dir)
        return video_path
        
    except Exception as e:
        raise Exception(f"YouTube download failed: {str(e)}")

def download_from_instagram(url):
    try:
        # Create Instagram loader instance
        L = instaloader.Instaloader()
        
        # Extract post shortcode from URL
        shortcode = url.split("/p/")[1].split("/")[0]
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, f"{shortcode}.mp4")
        
        # Download post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=temp_dir)
        
        # Find and return the video file
        for file in os.listdir(temp_dir):
            if file.endswith('.mp4'):
                return os.path.join(temp_dir, file)
        
        raise Exception("No video found in Instagram post")
        
    except Exception as e:
        raise Exception(f"Instagram download failed: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)