import os
import logging
from urllib.parse import urlparse
import hashlib
from sanic import Sanic
import aiohttp
from sanic.response import json, file_stream, json
from yt_dlp import YoutubeDL

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

app = Sanic("NanoVideoApi")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('NanoVideoApi')

# Configuration
DOWNLOADS_DIR = os.getenv('DOWNLOADS_DIR', 'downloads')
API_KEYS = os.getenv('API_KEYS', '').split(',')  # Comma-separated API keys
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')  # For CORS

# Ensure the downloads directory exists
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def is_valid_url(url):
    """Validate the URL to ensure it's a proper and supported video URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        return False

def is_authorized(request):
    """Check if the request contains a valid API key."""
    api_key = request.args.get('api_key') or request.headers.get('X-API-Key')
    if api_key in API_KEYS:
        return True
    else:
        return False

@app.middleware('response')
async def add_cors_headers(request, response):
    """Add CORS headers to responses."""
    origin = request.headers.get('origin')
    if origin in ALLOWED_HOSTS:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'

@app.route("/")
async def index(request):
    return json({"message": "Welcome to the NanoVideoApi!"})

@app.route("/share", methods=["GET", "POST", "OPTIONS"])
async def share_download(request):
    if request.method == 'OPTIONS':
        return json({}, status=204)
    
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    url = request.args.get("url") or request.json.get("url")
    if not url or not is_valid_url(url):
        return json({"error": "Invalid or missing URL parameter."}, status=400)
    
    logger.info(f"Initiating download for URL: {url}")
    
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOADS_DIR, '%(id)s.%(ext)s'),
        "format": "best",
        'logger': logger,
        'progress_hooks': [lambda d: logger.info(d)],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)
            logger.info(f"Download completed: {file_path}")
            return json({"message": "Download started.", "file": os.path.basename(file_path)})
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return json({"error": str(e)}, status=500)

@app.route("/files", methods=["GET"])
async def list_files(request):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    files = os.listdir(DOWNLOADS_DIR)
    files_info = []
    for f in files:
        file_path = os.path.join(DOWNLOADS_DIR, f)
        if os.path.isfile(file_path):
            files_info.append({
                "name": f,
                "size": os.path.getsize(file_path),
                "path": f"/files/{f}"
            })
    return json({"files": files_info})

@app.route("/files/<filename>", methods=["GET"])
async def get_file(request, filename):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if os.path.exists(file_path):
        return await file_stream(file_path, filename=filename)
    else:
        return json({"error": "File not found."}, status=404)

@app.route("/info", methods=["POST"])
async def get_info(request):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    url = request.json.get("url")
    if not url or not is_valid_url(url):
        return json({"error": "Invalid or missing URL parameter."}, status=400)
    
    ydl_opts = {"skip_download": True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return json(info)
    except Exception as e:
        logger.error(f"Error fetching info for {url}: {str(e)}")
        return json({"error": str(e)}, status=500)
    
@app.route("/download", methods=["GET", "POST"])
async def download_video(request):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    logger.info(f"Request: {request}")
    logger.info(f"Request URL: {request.url}")
    url = request.args.get("url")
    if not url or not is_valid_url(url):
        return json({"error": "Invalid or missing URL parameter."}, status=400)
    
    # Create a hash of the URL for the filename
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]  # Using first 16 chars of hash
    logger.info(f"Starting streaming download for URL: {url} (hash: {url_hash})")
    
    try:
        # First get video info
        with YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            ext = info.get('ext', 'mp4')
            cache_filename = f"{url_hash}.{ext}"
            file_path = os.path.join(DOWNLOADS_DIR, cache_filename)
            
            # Create response headers for streaming
            headers = {
                'Content-Type': 'video/mp4',
                'Content-Disposition': f'attachment; filename="{title}.{ext}"'
            }

            # Check if file exists in cache
            if os.path.exists(file_path):
                logger.info(f"Serving cached file: {file_path}")
                return await file_stream(file_path, headers=headers)
            
            logger.info(f"File not in cache, downloading: {url}")
            
            # Set up streaming options
            ydl_opts = {
                "format": "best",
                "quiet": True,
                "no_warnings": True,
                "outtmpl": file_path,  # Save to downloads directory with hash name
                "progress_hooks": [lambda d: logger.debug(f"Download progress: {d.get('status')}")],
            }

            # Download the file to cache
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Stream the cached file
            return await file_stream(file_path, headers=headers)

    except Exception as e:
        logger.error(f"Error streaming download for {url}: {str(e)}")
        return json({"error": str(e)}, status=500)

if __name__ == "__main__":
    # Use environment variables for host and port if set
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    app.run(host=host, port=port)
