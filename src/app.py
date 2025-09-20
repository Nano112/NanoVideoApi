import os
import logging
from urllib.parse import urlparse, urljoin
import hashlib
import time
import requests
import json
from sanic import Sanic
from sanic.response import json as json_response, file_stream, redirect
from yt_dlp import YoutubeDL
from pathlib import Path
import tempfile
import shutil

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

# Copyparty integration settings
USE_COPYPARTY = os.environ.get('USE_COPYPARTY', os.getenv('USE_COPYPARTY', 'false')).lower() == 'true'
COPYPARTY_URL = os.environ.get('COPYPARTY_URL', os.getenv('COPYPARTY_URL', 'http://localhost:3923'))
COPYPARTY_USERNAME = os.environ.get('COPYPARTY_USERNAME', os.getenv('COPYPARTY_USERNAME', ''))
COPYPARTY_PASSWORD = os.environ.get('COPYPARTY_PASSWORD', os.getenv('COPYPARTY_PASSWORD', ''))
COPYPARTY_FOLDER = os.environ.get('COPYPARTY_FOLDER', os.getenv('COPYPARTY_FOLDER', '/videos'))  # Path in copyparty

# Log startup configuration (without exposing API keys or passwords)
logger.info("="*50)
logger.info("NanoVideoApi Starting Up")
logger.info("="*50)
logger.info(f"Host: {HOST}")
logger.info(f"Port: {PORT}")
logger.info(f"Storage Mode: {'Copyparty' if USE_COPYPARTY else 'Local filesystem'}")
if USE_COPYPARTY:
    logger.info(f"Copyparty URL: {COPYPARTY_URL}")
    logger.info(f"Copyparty Folder: {COPYPARTY_FOLDER}")
    logger.info(f"Copyparty Auth: {'Configured' if COPYPARTY_USERNAME else 'Anonymous'}")
else:
    logger.info(f"Downloads Directory: {DOWNLOADS_DIR}")
logger.info(f"API Keys configured: {len([k for k in API_KEYS if k.strip()])}")
logger.info(f"Allowed Hosts: {ALLOWED_HOSTS}")
logger.info("="*50)

# Application startup time for health checks
app_start_time = time.time()

# Ensure the downloads directory exists if not using copyparty
if not USE_COPYPARTY:
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

def upload_to_copyparty(file_path, filename=None):
    """Upload a file to copyparty and return the URL."""
    if filename is None:
        filename = os.path.basename(file_path)
    
    upload_url = urljoin(COPYPARTY_URL, COPYPARTY_FOLDER)
    
    # Prepare auth
    auth = None
    if COPYPARTY_USERNAME and COPYPARTY_PASSWORD:
        auth = (COPYPARTY_USERNAME, COPYPARTY_PASSWORD)
    elif COPYPARTY_PASSWORD:
        # Copyparty allows password-only auth
        auth = (COPYPARTY_PASSWORD, 'k')
    
    # Upload file
    try:
        with open(file_path, 'rb') as f:
            # Using multipart upload for compatibility
            files = {'f': (filename, f)}
            params = {'want': 'url'}  # Request direct URL in response
            
            response = requests.post(
                upload_url,
                files=files,
                params=params,
                auth=auth
            )
            
            # Copyparty returns 201 (Created) for successful uploads
            if response.status_code in [200, 201]:
                # Copyparty returns the URL directly with want=url
                file_url = response.text.strip()
                logger.info(f"✅ Uploaded to copyparty: {file_url}")
                return file_url
            else:
                logger.error(f"Failed to upload to copyparty: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error uploading to copyparty: {e}")
        return None

def list_copyparty_files():
    """List files in the copyparty folder."""
    try:
        list_url = urljoin(COPYPARTY_URL, COPYPARTY_FOLDER)
        params = {'ls': 't'}  # Get plaintext listing
        
        auth = None
        if COPYPARTY_USERNAME and COPYPARTY_PASSWORD:
            auth = (COPYPARTY_USERNAME, COPYPARTY_PASSWORD)
        elif COPYPARTY_PASSWORD:
            auth = (COPYPARTY_PASSWORD, 'k')
        
        response = requests.get(list_url, params=params, auth=auth)
        
        if response.status_code == 200:
            # Parse the plaintext listing
            files = []
            for line in response.text.strip().split('\n'):
                if line and not line.startswith('#'):
                    # Basic parsing - you might need to adjust based on actual format
                    parts = line.split()
                    if len(parts) > 0:
                        filename = parts[-1]
                        files.append({
                            "name": filename,
                            "path": urljoin(list_url + '/', filename)
                        })
            return files
        else:
            logger.error(f"Failed to list copyparty files: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error listing copyparty files: {e}")
        return []

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
    storage_info = f"Using {'Copyparty' if USE_COPYPARTY else 'local'} storage"
    return json_response({
        "message": "Welcome to the NanoVideoApi!", 
        "version": "1.0.0",
        "storage": storage_info
    })

@app.route("/health")
async def health_check(request):
    """Health check endpoint for container orchestration."""
    uptime = time.time() - app_start_time
    
    # Check storage availability
    storage_available = True
    if USE_COPYPARTY:
        # Try to ping copyparty
        try:
            response = requests.get(COPYPARTY_URL, timeout=5)
            storage_available = response.status_code == 200
        except:
            storage_available = False
    else:
        storage_available = os.access(DOWNLOADS_DIR, os.W_OK)
    
    health_status = {
        "status": "healthy" if storage_available else "unhealthy",
        "uptime_seconds": round(uptime, 2),
        "storage_mode": "copyparty" if USE_COPYPARTY else "local",
        "storage_available": storage_available,
        "api_version": "1.0.0",
        "environment": {
            "host": HOST,
            "port": PORT,
            "api_keys_count": len([k for k in API_KEYS if k.strip()])
        }
    }
    
    if USE_COPYPARTY:
        health_status["environment"]["copyparty_url"] = COPYPARTY_URL
    else:
        health_status["environment"]["downloads_dir"] = DOWNLOADS_DIR
    
    logger.info(f"🏥 Health check - Status: {'healthy' if storage_available else 'unhealthy'}")
    
    if not storage_available:
        return json_response(health_status, status=503)
    
    return json_response(health_status)

@app.route("/share", methods=["GET", "POST", "OPTIONS"])
async def share_download(request):
    if request.method == 'OPTIONS':
        return json_response({}, status=204)
    
    if not is_authorized(request):
        return json_response({"error": "Unauthorized."}, status=401)
    
    url = request.args.get("url") or (request.json.get("url") if request.json else None)
    if not url or not is_valid_url(url):
        logger.warning(f"❌ Invalid URL provided: {url}")
        return json_response({"error": "Invalid or missing URL parameter."}, status=400)
    
    logger.info(f"🎬 Initiating download for URL: {url}")
    
    # Use temp directory if using copyparty, otherwise use configured directory
    download_dir = tempfile.gettempdir() if USE_COPYPARTY else DOWNLOADS_DIR
    
    ydl_opts = {
        "outtmpl": os.path.join(download_dir, '%(id)s.%(ext)s'),
        "format": "best",
        'logger': logger,
        'progress_hooks': [lambda d: logger.info(f"📊 Download progress: {d.get('status')}")],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)
            
            if USE_COPYPARTY:
                # Upload to copyparty and get URL
                copyparty_url = upload_to_copyparty(file_path)
                
                # Clean up temp file
                try:
                    os.remove(file_path)
                except:
                    pass
                
                if copyparty_url:
                    return json_response({
                        "message": "Download completed and uploaded to copyparty.",
                        "url": copyparty_url,
                        "filename": os.path.basename(file_path)
                    })
                else:
                    return json_response({"error": "Failed to upload to copyparty"}, status=500)
            else:
                # Local storage mode
                logger.info(f"✅ Download completed: {file_path}")
                return json_response({
                    "message": "Download completed.",
                    "file": os.path.basename(file_path)
                })
                
    except Exception as e:
        logger.error(f"💥 Error downloading {url}: {str(e)}")
        return json_response({"error": str(e)}, status=500)

@app.route("/files", methods=["GET"])
async def list_files(request):
    if not is_authorized(request):
        return json_response({"error": "Unauthorized."}, status=401)
    
    logger.info("📁 Listing cached files")
    
    if USE_COPYPARTY:
        # List files from copyparty
        files_info = list_copyparty_files()
    else:
        # List local files
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
    return json_response({"files": files_info})

@app.route("/files/<filename>", methods=["GET"])
async def get_file(request, filename):
    if not is_authorized(request):
        return json_response({"error": "Unauthorized."}, status=401)
    
    logger.info(f"📄 Serving file: {filename}")
    
    if USE_COPYPARTY:
        # Redirect to copyparty URL
        file_url = urljoin(COPYPARTY_URL, f"{COPYPARTY_FOLDER}/{filename}")
        
        # Add auth params if needed
        if COPYPARTY_PASSWORD:
            if COPYPARTY_USERNAME:
                file_url += f"?pw={COPYPARTY_USERNAME}:{COPYPARTY_PASSWORD}"
            else:
                file_url += f"?pw={COPYPARTY_PASSWORD}"
        
        return redirect(file_url)
    else:
        # Serve from local storage
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.exists(file_path):
            return await file_stream(file_path, filename=filename)
        else:
            logger.warning(f"❌ File not found: {filename}")
            return json_response({"error": "File not found."}, status=404)

@app.route("/info", methods=["POST"])
async def get_info(request):
    if not is_authorized(request):
        return json_response({"error": "Unauthorized."}, status=401)
    
    if not request.json:
        return json_response({"error": "JSON body required."}, status=400)
    
    url = request.json.get("url")
    if not url or not is_valid_url(url):
        logger.warning(f"❌ Invalid URL for info: {url}")
        return json_response({"error": "Invalid or missing URL parameter."}, status=400)
    
    logger.info(f"ℹ️ Getting info for URL: {url}")
    
    ydl_opts = {"skip_download": True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"✅ Info retrieved for: {info.get('title', 'Unknown')}")
            return json_response(info)
    except Exception as e:
        logger.error(f"💥 Error fetching info for {url}: {str(e)}")
        return json_response({"error": str(e)}, status=500)
    
@app.route("/download", methods=["GET", "POST"])
async def download_video(request):
    if not is_authorized(request):
        return json_response({"error": "Unauthorized."}, status=401)
    
    url = request.args.get("url")
    if not url or not is_valid_url(url):
        logger.warning(f"❌ Invalid URL for download: {url}")
        return json_response({"error": "Invalid or missing URL parameter."}, status=400)
    
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
            
            if USE_COPYPARTY:
                # For copyparty mode, check if file exists there
                copyparty_file_url = urljoin(COPYPARTY_URL, f"{COPYPARTY_FOLDER}/{cache_filename}")
                
                # Try to check if file exists in copyparty
                auth = None
                if COPYPARTY_USERNAME and COPYPARTY_PASSWORD:
                    auth = (COPYPARTY_USERNAME, COPYPARTY_PASSWORD)
                elif COPYPARTY_PASSWORD:
                    auth = (COPYPARTY_PASSWORD, 'k')
                
                try:
                    response = requests.head(copyparty_file_url, auth=auth)
                    if response.status_code == 200:
                        logger.info(f"🎯 File exists in copyparty: {cache_filename}")
                        return redirect(copyparty_file_url)
                except:
                    pass
                
                # Download to temp then upload to copyparty
                temp_path = os.path.join(tempfile.gettempdir(), cache_filename)
                
                logger.info(f"⬇️ Downloading to temp: {url}")
                ydl_opts = {
                    "format": "best",
                    "quiet": True,
                    "no_warnings": True,
                    "outtmpl": temp_path,
                }
                
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Upload to copyparty
                copyparty_url = upload_to_copyparty(temp_path, cache_filename)
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if copyparty_url:
                    return redirect(copyparty_url)
                else:
                    return json_response({"error": "Failed to upload to copyparty"}, status=500)
                    
            else:
                # Local storage mode - original behavior
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
        return json_response({"error": str(e)}, status=500)

if __name__ == "__main__":
    logger.info(f"🚀 Starting NanoVideoApi on {HOST}:{PORT}")
    logger.info(f"📦 Storage mode: {'Copyparty' if USE_COPYPARTY else 'Local filesystem'}")
    app.run(host=HOST, port=PORT, debug=False)