import os
import logging
from urllib.parse import urlparse
import hashlib
import time
from sanic import Sanic
from sanic.response import json, file_stream
from yt_dlp import YoutubeDL

# Load environment variables from .env file if it exists, but prioritize actual env vars
from dotenv import load_dotenv
load_dotenv()

app = Sanic("NanoVideoApi")

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NanoVideoApi')

# Configuration - prioritize environment variables over .env file
DOWNLOADS_DIR = os.environ.get('DOWNLOADS_DIR', os.getenv('DOWNLOADS_DIR', 'downloads'))
API_KEYS = os.environ.get('API_KEYS', os.getenv('API_KEYS', '')).split(',')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', os.getenv('ALLOWED_HOSTS', '')).split(',')
HOST = os.environ.get('HOST', os.getenv('HOST', '0.0.0.0'))
PORT = int(os.environ.get('API_PORT', os.getenv('API_PORT', '8000')))

# Log startup configuration (without exposing API keys)
logger.info("="*50)
logger.info("NanoVideoApi Starting Up")
logger.info("="*50)
logger.info(f"Host: {HOST}")
logger.info(f"Port: {PORT}")
logger.info(f"Downloads Directory: {DOWNLOADS_DIR}")
logger.info(f"API Keys configured: {len([k for k in API_KEYS if k.strip()])}")
logger.info(f"Allowed Hosts: {ALLOWED_HOSTS}")
logger.info("="*50)

# Application startup time for health checks
app_start_time = time.time()

# Ensure the downloads directory exists
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)
    logger.info(f"Created downloads directory: {DOWNLOADS_DIR}")

def is_valid_url(url):
    """Validate the URL to ensure it's a proper and supported video URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"URL validation error for {url}: {e}")
        return False

def is_authorized(request):
    """Check if the request contains a valid API key."""
    api_key = request.args.get('api_key') or request.headers.get('X-API-Key')
    is_valid = api_key in API_KEYS and api_key.strip() != ''
    
    if not is_valid:
        logger.warning(f"Unauthorized request from {request.ip} - API key: {api_key[:8] if api_key else 'None'}...")
    
    return is_valid

@app.middleware('request')
async def log_request(request):
    """Log all incoming requests."""
    logger.info(f"📥 {request.method} {request.path} - IP: {request.ip} - User-Agent: {request.headers.get('User-Agent', 'Unknown')[:50]}")

@app.middleware('response')
async def log_response(request, response):
    """Log responses and add CORS headers."""
    # Log response
    logger.info(f"📤 {request.method} {request.path} - Status: {response.status} - IP: {request.ip}")
    
    # Add CORS headers
    origin = request.headers.get('origin')
    if origin in ALLOWED_HOSTS:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'

@app.route("/")
async def index(request):
    logger.info("🏠 Index endpoint accessed")
    return json({"message": "Welcome to the NanoVideoApi!", "version": "1.0.0"})

@app.route("/health")
async def health_check(request):
    """Health check endpoint for container orchestration."""
    uptime = time.time() - app_start_time
    
    # Check if downloads directory is accessible
    downloads_writable = os.access(DOWNLOADS_DIR, os.W_OK)
    
    health_status = {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "downloads_dir_writable": downloads_writable,
        "api_version": "1.0.0",
        "environment": {
            "host": HOST,
            "port": PORT,
            "downloads_dir": DOWNLOADS_DIR,
            "api_keys_count": len([k for k in API_KEYS if k.strip()])
        }
    }
    
    logger.info(f"🏥 Health check - Status: {'healthy' if downloads_writable else 'unhealthy'}")
    
    # If critical components are not working, return unhealthy status
    if not downloads_writable:
        health_status["status"] = "unhealthy"
        return json(health_status, status=503)
    
    return json(health_status)

@app.route("/share", methods=["GET", "POST", "OPTIONS"])
async def share_download(request):
    if request.method == 'OPTIONS':
        return json({}, status=204)
    
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    url = request.args.get("url") or (request.json.get("url") if request.json else None)
    if not url or not is_valid_url(url):
        logger.warning(f"❌ Invalid URL provided: {url}")
        return json({"error": "Invalid or missing URL parameter."}, status=400)
    
    logger.info(f"🎬 Initiating download for URL: {url}")
    
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOADS_DIR, '%(id)s.%(ext)s'),
        "format": "best",
        'logger': logger,
        'progress_hooks': [lambda d: logger.info(f"📊 Download progress: {d.get('status')}")],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)
            logger.info(f"✅ Download completed: {file_path}")
            return json({"message": "Download started.", "file": os.path.basename(file_path)})
    except Exception as e:
        logger.error(f"💥 Error downloading {url}: {str(e)}")
        return json({"error": str(e)}, status=500)

@app.route("/files", methods=["GET"])
async def list_files(request):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    logger.info("📁 Listing cached files")
    
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
    
    logger.info(f"📁 Found {len(files_info)} cached files")
    return json({"files": files_info})

@app.route("/files/<filename>", methods=["GET"])
async def get_file(request, filename):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    logger.info(f"📄 Serving file: {filename}")
    
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if os.path.exists(file_path):
        return await file_stream(file_path, filename=filename)
    else:
        logger.warning(f"❌ File not found: {filename}")
        return json({"error": "File not found."}, status=404)

@app.route("/info", methods=["POST"])
async def get_info(request):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    if not request.json:
        return json({"error": "JSON body required."}, status=400)
    
    url = request.json.get("url")
    if not url or not is_valid_url(url):
        logger.warning(f"❌ Invalid URL for info: {url}")
        return json({"error": "Invalid or missing URL parameter."}, status=400)
    
    logger.info(f"ℹ️ Getting info for URL: {url}")
    
    ydl_opts = {"skip_download": True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"✅ Info retrieved for: {info.get('title', 'Unknown')}")
            return json(info)
    except Exception as e:
        logger.error(f"💥 Error fetching info for {url}: {str(e)}")
        return json({"error": str(e)}, status=500)
    
@app.route("/download", methods=["GET", "POST"])
async def download_video(request):
    if not is_authorized(request):
        return json({"error": "Unauthorized."}, status=401)
    
    url = request.args.get("url")
    if not url or not is_valid_url(url):
        logger.warning(f"❌ Invalid URL for download: {url}")
        return json({"error": "Invalid or missing URL parameter."}, status=400)
    
    # Create a hash of the URL for the filename
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    logger.info(f"🎯 Starting streaming download for URL: {url} (hash: {url_hash})")
    
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
                logger.info(f"🎯 Serving cached file: {cache_filename}")
                return await file_stream(file_path, headers=headers)
            
            logger.info(f"⬇️ File not in cache, downloading: {url}")
            
            # Set up streaming options
            ydl_opts = {
                "format": "best",
                "quiet": True,
                "no_warnings": True,
                "outtmpl": file_path,
                "progress_hooks": [lambda d: logger.info(f"📊 Download progress: {d.get('status')}")],
            }

            # Download the file to cache
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            logger.info(f"✅ Download completed, streaming: {cache_filename}")
            # Stream the cached file
            return await file_stream(file_path, headers=headers)

    except Exception as e:
        logger.error(f"💥 Error streaming download for {url}: {str(e)}")
        return json({"error": str(e)}, status=500)

if __name__ == "__main__":
    logger.info(f"🚀 Starting NanoVideoApi on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
