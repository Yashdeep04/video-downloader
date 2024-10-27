from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
import os
import tempfile

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Video Downloader API is running!"

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({'error': 'Empty URL provided'}), 400
        
        if 'youtube.com' in url or 'youtu.be' in url:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Download YouTube video
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()
            
            if not stream:
                return jsonify({'error': 'No suitable video stream found'}), 400
                
            # Download to temporary file
            video_path = stream.download(output_path=temp_dir)
            
            return send_file(
                video_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4'
            )
        else:
            return jsonify({'error': 'Only YouTube videos are supported for now'}), 400
            
    except Exception as e:
        print(f"Error: {str(e)}")  # This will show in Render logs
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
