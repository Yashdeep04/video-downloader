from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import instaloader
import os
import tempfile
from pytube import YouTube
import re

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
        temp_dir = tempfile.mkdtemp()
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable video stream found")
            
        video_path = stream.download(output_path=temp_dir)
        return video_path
        
    except Exception as e:
        raise Exception(f"YouTube download failed: {str(e)}")

def download_from_instagram(url):
    try:
        L = instaloader.Instaloader()
        
        # Handle both regular posts and reels
        if '/reel/' in url:
            # Extract the shortcode from reel URL
            shortcode = re.search(r'/reel/([^/?]+)', url).group(1)
        else:
            # Extract shortcode from regular post URL
            shortcode = re.search(r'/p/([^/?]+)', url).group(1)
        
        temp_dir = tempfile.mkdtemp()
        
        # Download the post or reel
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        if hasattr(post, 'video_url'):
            # For video posts and reels
            import requests
            video_response = requests.get(post.video_url)
            video_path = os.path.join(temp_dir, f"{shortcode}.mp4")
            
            with open(video_path, 'wb') as f:
                f.write(video_response.content)
            
            return video_path
        else:
            raise Exception("This post doesn't contain a video")
        
    except Exception as e:
        raise Exception(f"Instagram download failed: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
