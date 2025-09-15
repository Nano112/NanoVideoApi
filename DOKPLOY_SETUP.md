# Dokploy Deployment Setup for NanoVideoApi

## ✅ Ready for Deployment

Your NanoVideoApi is now configured for production deployment with Dokploy!

## 🔧 Dokploy Environment Variables

Set these in your Dokploy "Environment Settings" panel:

```
API_KEYS=your-secure-api-key-1,your-secure-api-key-2
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
HOST=0.0.0.0
PORT=8000
DOWNLOADS_DIR=/app/downloads
```

**Important**: These environment variables will override any hardcoded values in docker-compose.yml!

## 💾 Persistent Storage

The docker-compose.yml now uses **named volumes** for persistence:

- `nanovideo_downloads` - Stores downloaded video files
- `nanovideo_logs` - Stores application logs

These volumes will **persist across deployments**, so your cached files won't be lost when you update the application.

## 📊 Monitoring & Logs

### Health Endpoint
- `GET /health` - Returns detailed status including environment configuration
- Used by Docker for health checks every 30 seconds

### Application Logs
Your app now logs:
- ✅ **Startup configuration** (with API key count, not actual keys)
- 📥 **All incoming requests** with IP, method, path, and User-Agent
- 📤 **All responses** with status codes
- ⚠️ **Unauthorized attempts** with partial API key info
- 🎬 **Video download operations** with progress
- 🏥 **Health check status**

### Example Log Output
```
2025-09-15 13:25:04 - NanoVideoApi - INFO - ==================================================
2025-09-15 13:25:04 - NanoVideoApi - INFO - NanoVideoApi Starting Up
2025-09-15 13:25:04 - NanoVideoApi - INFO - Host: 0.0.0.0
2025-09-15 13:25:04 - NanoVideoApi - INFO - Port: 8000
2025-09-15 13:25:04 - NanoVideoApi - INFO - Downloads Directory: /app/downloads
2025-09-15 13:25:04 - NanoVideoApi - INFO - API Keys configured: 2
2025-09-15 13:25:04 - NanoVideoApi - INFO - Allowed Hosts: ['yourdomain.com']
2025-09-15 13:25:04 - NanoVideoApi - INFO - ==================================================

2025-09-15 13:25:09 - NanoVideoApi - INFO - 📥 GET /download - IP: 192.168.1.100 - User-Agent: MyApp/1.0
2025-09-15 13:25:09 - NanoVideoApi - INFO - 🎯 Starting streaming download for URL: https://example.com/video
2025-09-15 13:25:12 - NanoVideoApi - INFO - ✅ Download completed, streaming: abc123.mp4
2025-09-15 13:25:12 - NanoVideoApi - INFO - 📤 GET /download - Status: 200 - IP: 192.168.1.100
```

## 🚀 Deployment Steps

1. **Push your code to Git**:
   ```bash
   git add .
   git commit -m "Add production setup with persistent volumes"
   git push origin main
   ```

2. **In Dokploy**:
   - Create new application
   - Connect your Git repository
   - Set environment variables in "Environment Settings"
   - Deploy!

3. **Verify deployment**:
   - Check health: `curl https://yourapp.domain.com/health`
   - Test API: `curl "https://yourapp.domain.com/?api_key=your-key"`

## 🔐 Security Notes

- **API Keys**: Use strong, random keys in production
- **ALLOWED_HOSTS**: Set specific domains instead of `*`
- **HTTPS**: Always deploy behind HTTPS in production
- **Logs**: Monitor unauthorized access attempts

## 📈 Scaling

For high traffic, you can:
1. Switch to `Dockerfile.gunicorn` for multi-worker setup
2. Set `WORKERS` environment variable (recommended: CPU cores × 2)
3. Monitor memory usage and adjust accordingly

## 🎯 API Endpoints

Once deployed:
- `GET /health` - Health check (no auth required)
- `GET /?api_key=KEY` - Welcome message
- `POST /info` - Get video information
- `GET /download?url=URL&api_key=KEY` - Download and stream video
- `GET /files?api_key=KEY` - List cached files
- `GET /files/{filename}?api_key=KEY` - Get cached file

## 📦 Files Ready for Deployment

- ✅ `Dockerfile` - Production Docker build
- ✅ `docker-compose.yml` - With persistent named volumes
- ✅ `src/app.py` - Enhanced with logging and environment variable support
- ✅ `requirements.txt` - All dependencies
- ✅ `.dockerignore` - Optimized build context
- ✅ `.env.example` - Environment template

Your NanoVideoApi is production-ready! 🎉
