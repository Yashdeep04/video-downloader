from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import instaloader
import os
import tempfile
from pytube import YouTube
import re
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def create_instagram_session():
    L = instaloader.Instaloader()
    # Add these basic headers to mimic a browser request
    L.context._session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })
    return L

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
        temp_dir = tempfile.mkdtemp()
        
        # Create a session with proper headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

        # For reels
        if '/reel/' in url:
            # Extract the shortcode
            shortcode = re.search(r'/reel/([^/?]+)', url).group(1)
            api_url = f"https://www.instagram.com/graphql/query/?query_hash=b3055c01b4b222b8a47dc12b090e4e64&variables={{\"shortcode\":\"{shortcode}\"}}"
            
            response = session.get(api_url)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch reel data: HTTP {response.status_code}")
            
            data = response.json()
            try:
                video_url = data['data']['shortcode_media']['video_url']
            except (KeyError, TypeError):
                raise Exception("Could not find video URL in Instagram response")

        # For regular posts
        else:
            L = create_instagram_session()
            if '/p/' in url:
                shortcode = re.search(r'/p/([^/?]+)', url).group(1)
            else:
                raise Exception("Invalid Instagram URL format")

            post = instaloader.Post.from_shortcode(L.context, shortcode)
            video_url = post.video_url
            
            if not video_url:
                raise Exception("No video found in this Instagram post")

        # Download the video
        video_response = session.get(video_url, stream=True)
        if video_response.status_code != 200:
            raise Exception("Failed to download video file")

        video_path = os.path.join(temp_dir, f"instagram_video_{datetime.now().timestamp()}.mp4")
        
        with open(video_path, 'wb') as video_file:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    video_file.write(chunk)

        return video_path

    except Exception as e:
        raise Exception(f"Instagram download failed: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
