from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import instaloader
import os
import tempfile
from pytube import YouTube
import re
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def create_instagram_session():
    L = instaloader.Instaloader()
    L.context._session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    return L

@app.route('/download', methods=['POST', 'OPTIONS'])
def download_video():
    if request.method == 'OPTIONS':
        return handle_preflight()

    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400

        url = data['url']
        logger.info(f"Received download request for URL: {url}")

        if 'youtube.com' in url or 'youtu.be' in url:
            video_path = download_from_youtube(url)
        elif 'instagram.com' in url:
            video_path = download_from_instagram(url)
        else:
            return jsonify({'error': 'Unsupported URL'}), 400

        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            attachment_filename='video.mp4'
        )

    except Exception as e:
        logger.error(f"Download failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def handle_preflight():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response

def download_from_youtube(url):
    try:
        logger.info("Starting YouTube download")
        temp_dir = tempfile.mkdtemp()
        yt = YouTube(url)
        
        # Get highest quality progressive stream
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable video stream found")
        
        video_path = stream.download(output_path=temp_dir)
        logger.info(f"YouTube download completed: {video_path}")
        return video_path
    
    except Exception as e:
        logger.error(f"YouTube download failed: {str(e)}", exc_info=True)
        raise Exception(f"YouTube download failed: {str(e)}")

def download_from_instagram(url):
    try:
        logger.info("Starting Instagram download")
        temp_dir = tempfile.mkdtemp()
        session = create_instagram_session()

        # Extract the shortcode from the URL
        if '/reel/' in url:
            shortcode = re.search(r'/reel/([^/?]+)', url).group(1)
        elif '/p/' in url:
            shortcode = re.search(r'/p/([^/?]+)', url).group(1)
        else:
            raise Exception("Invalid Instagram URL format")

        logger.info(f"Extracted shortcode: {shortcode}")

        # Try multiple methods to get the video
        video_path = None
        errors = []

        # Method 1: Try using instaloader
        try:
            L = create_instagram_session()
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            if post.is_video:
                video_path = os.path.join(temp_dir, f"video_{datetime.now().timestamp()}.mp4")
                L.download_post(post, target=temp_dir)
                logger.info("Successfully downloaded using instaloader")
                return video_path
        except Exception as e:
            errors.append(f"Instaloader method failed: {str(e)}")
            logger.warning("Instaloader method failed, trying alternative method")

        # Method 2: Try using direct API request
        try:
            session = requests.Session()
            session.headers.update(create_instagram_session().context._session.headers)
            
            response = session.get(f"https://www.instagram.com/p/{shortcode}/?__a=1")
            if response.status_code == 200:
                data = response.json()
                video_url = data['graphql']['shortcode_media']['video_url']
                
                video_path = os.path.join(temp_dir, f"video_{datetime.now().timestamp()}.mp4")
                with open(video_path, 'wb') as f:
                    video_response = session.get(video_url, stream=True)
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info("Successfully downloaded using API method")
                return video_path
        except Exception as e:
            errors.append(f"API method failed: {str(e)}")
            logger.warning("API method failed")

        if not video_path:
            raise Exception(f"All download methods failed: {'; '.join(errors)}")

        return video_path

    except Exception as e:
        logger.error(f"Instagram download failed: {str(e)}", exc_info=True)
        raise Exception(f"Instagram download failed: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
