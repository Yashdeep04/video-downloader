from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import os
import tempfile
import logging
import time
from functools import wraps
import random

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def retry_on_error(max_retries=3, delay_seconds=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        raise e
                    logger.info(f"Attempt {attempt + 1} failed, retrying after delay...")
                    # Add random delay to avoid hitting rate limits
                    time.sleep(delay_seconds + random.uniform(0, 2))
            return func(*args, **kwargs)
        return wrapper
    return decorator

@retry_on_error(max_retries=3, delay_seconds=2)
def download_youtube_video(url, temp_dir):
    yt = YouTube(url)
    # Add a small delay after creating YouTube object
    time.sleep(1)
    
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    if not stream:
        raise Exception("No suitable video stream found")
    
    # Add a small delay before downloading
    time.sleep(1)
    
    video_path = stream.download(output_path=temp_dir)
    return video_path

@app.route('/')
def home():
    return "Video Downloader API is running!"

@app.route('/download', methods=['POST'])
def download_video():
    try:
        logger.info("Received download request")
        
        data = request.get_json()
        if not data or 'url' not in data:
            logger.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url'].strip()
        logger.info(f"Processing URL: {url}")
        
        if not url:
            logger.error("Empty URL provided")
            return jsonify({'error': 'Empty URL provided'}), 400
        
        if 'youtube.com' in url or 'youtu.be' in url:
            try:
                temp_dir = tempfile.mkdtemp()
                logger.info(f"Created temp directory: {temp_dir}")
                
                video_path = download_youtube_video(url, temp_dir)
                logger.info(f"Video downloaded to: {video_path}")
                
                if not os.path.exists(video_path):
                    logger.error("Downloaded file not found")
                    return jsonify({'error': 'Failed to download video'}), 500
                
                logger.info("Sending file")
                response = send_file(
                    video_path,
                    mimetype='video/mp4',
                    as_attachment=True,
                    download_name='video.mp4'
                )
                
                # Add CORS headers to response
                response.headers.add('Access-Control-Allow-Origin', 'https://yashdeep04.github.io')
                return response
                
            except Exception as e:
                logger.error(f"Error in YouTube download: {str(e)}")
                return jsonify({'error': f'YouTube download failed: {str(e)}'}), 500
                
        else:
            logger.error("Unsupported URL type")
            return jsonify({'error': 'Only YouTube videos are supported for now'}), 400
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
