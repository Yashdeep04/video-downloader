from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import instaloader
import os
import tempfile
import re

app = Flask(__name__)
CORS(app)

def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url))

def is_valid_instagram_url(url):
    instagram_regex = (
        r'(https?://)?(www\.)?instagram\.com/(p|reel)/[A-Za-z0-9_-]+'
    )
    return bool(re.match(instagram_regex, url))

def download_from_youtube(url):
    try:
        temp_dir = tempfile.mkdtemp()
        yt = YouTube(url)
        
        # Get the highest quality progressive stream
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
        L = instaloader.Instaloader()
        
        # Extract shortcode from URL
        shortcode = url.split("/p/")[1].split("/")[0] if "/p/" in url else url.split("/reel/")[1].split("/")[0]
        
        temp_dir = tempfile.mkdtemp()
        
        # Download post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if not post.is_video:
            raise Exception("This Instagram post does not contain a video")
            
        L.download_post(post, target=temp_dir)
        
        # Find the video file
        for file in os.listdir(temp_dir):
            if file.endswith('.mp4'):
                return os.path.join(temp_dir, file)
        
        raise Exception("No video found in Instagram post")
    
    except Exception as e:
        raise Exception(f"Instagram download failed: {str(e)}")

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({'error': 'Empty URL provided'}), 400
        
        if is_valid_youtube_url(url):
            video_path = download_from_youtube(url)
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4'
            )
        
        elif is_valid_instagram_url(url):
            video_path = download_from_instagram(url)
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4'
            )
        
        else:
            return jsonify({'error': 'Invalid URL. Only YouTube and Instagram URLs are supported.'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
