from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def download_video(url, temp_dir):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            logger.info("Starting download with yt-dlp")
            info = ydl.extract_info(url, download=True)
            video_path = os.path.join(temp_dir, f"{info['title']}.mp4")
            logger.info(f"Download completed: {video_path}")
            return video_path
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise

@app.route('/')
def home():
    return "Video Downloader API is running!"

@app.route('/download', methods=['POST'])
def download_video_route():
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
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        
        try:
            video_path = download_video(url, temp_dir)
            
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
            logger.error(f"Error in video download: {str(e)}")
            return jsonify({'error': f'Download failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
