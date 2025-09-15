# Deployment Guide for NanoVideoApi

## 🚀 Quick Deployment Summary

Your NanoVideoApi is now production-ready! Here's what has been set up:

## ✅ What's Been Created

### Core Files
- `Dockerfile` - Multi-stage production Docker build (uses Sanic directly)
- `Dockerfile.gunicorn` - Alternative with Gunicorn for high-scale deployments
- `docker-compose.yml` - Local testing setup
- `start.sh` - Gunicorn startup script (for use with Dockerfile.gunicorn)
- `.dockerignore` - Optimized build context
- `.env.example` - Environment configuration template
- `README.md` - Complete documentation

### Application Updates
- Added `/health` endpoint for container health checks
- Fixed imports and dependencies
- Production-ready configuration
- Security hardening (non-root user, proper permissions)

## 🐳 Dokploy Deployment Steps

1. **Prepare Your Environment**
   ```bash
   # Copy and customize environment file
   cp .env.example .env
   # Edit with your secure API keys
   ```

2. **Push to Git Repository**
   ```bash
   git add .
   git commit -m "Add production Docker setup"
   git push origin main
   ```

3. **Configure in Dokploy**
   - Create new application in Dokploy
   - Connect your Git repository
   - Set environment variables:
     ```
     API_KEYS=your-super-secure-api-key-here
     ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
     HOST=0.0.0.0
     PORT=8000
     ```

4. **Deploy**
   - Dokploy will automatically detect the Dockerfile
   - Build and deploy process will start automatically
   - Health checks will ensure proper deployment

## 🧪 Local Testing

### Docker Compose (Recommended)
```bash
# Build and run
docker-compose up --build

# Test health endpoint
curl http://localhost:8001/health

# Test API endpoint (replace with your API key)
curl "http://localhost:8001/?api_key=your-api-key-here"
```

### Docker Build & Run
```bash
# Build image
docker build -t nanovideo-api .

# Run container
docker run -p 8000:8000 \
  -e API_KEYS=test-key \
  -e "ALLOWED_HOSTS=*" \
  nanovideo-api
```

## 📈 Scaling Options

### Option 1: Sanic Direct (Default - Dockerfile)
- Simple deployment
- Good for small to medium traffic
- Lower memory footprint
- Easier debugging

### Option 2: Gunicorn + Sanic (Dockerfile.gunicorn)
For high-traffic deployments:
```bash
# Build with Gunicorn
docker build -f Dockerfile.gunicorn -t nanovideo-api-gunicorn .

# Run with worker configuration
docker run -p 8000:8000 \
  -e API_KEYS=your-api-key \
  -e WORKERS=8 \
  -e "ALLOWED_HOSTS=yourdomain.com" \
  nanovideo-api-gunicorn
```

## 🔧 Configuration Options

### Environment Variables
| Variable | Production Example | Description |
|----------|-------------------|-------------|
| `API_KEYS` | `key1,key2,key3` | Secure API keys |
| `ALLOWED_HOSTS` | `api.yourdomain.com` | Specific domains for CORS |
| `WORKERS` | `4` | Gunicorn workers (CPU cores × 2) - only for Gunicorn setup |
| `PORT` | `8000` | Application port |

### Performance Tuning
- **Default Setup**: Single-process Sanic (good for most use cases)
- **High-traffic Setup**: Use Dockerfile.gunicorn with multiple workers
- **Memory**: ~256MB for default, ~512MB per worker for Gunicorn
- **Storage**: Monitor downloads directory growth

## 📊 Monitoring

### Health Checks
- Endpoint: `GET /health`
- Docker health check: Built-in every 30 seconds
- Returns application uptime and system status

Example response:
```json
{
  "status": "healthy",
  "uptime_seconds": 123.45,
  "downloads_dir_writable": true,
  "api_version": "1.0.0"
}
```

### Logs
- Default setup: stdout/stderr (visible with `docker logs`)
- Gunicorn setup: `/app/logs/access.log` and `/app/logs/error.log`

## 🔒 Security Checklist

- [x] Non-root user in container
- [x] API key authentication required
- [x] Removed unused dependencies
- [ ] Update ALLOWED_HOSTS for production (replace `*`)
- [ ] Use secure, random API keys
- [ ] Deploy behind HTTPS reverse proxy
- [ ] Consider implementing rate limiting

## 🎯 API Endpoints

Once deployed, your API will have these endpoints:

```bash
# Health check (no auth required)
GET /health

# Welcome message
GET /?api_key=your-api-key

# Get video info (requires API key)
POST /info
Content-Type: application/json
X-API-Key: your-api-key
{"url": "https://youtube.com/watch?v=..."}

# Download and stream video
GET /download?url=https://youtube.com/watch?v=...&api_key=your-api-key

# List cached files
GET /files?api_key=your-api-key

# Get specific cached file
GET /files/{filename}?api_key=your-api-key
```

## 🔄 Updates and Maintenance

### Updating the Application
1. Make changes to your code
2. Commit and push to Git
3. Dokploy will auto-deploy on push (if configured)
4. Or manually trigger deployment in Dokploy dashboard

### Switching to High-Scale Setup
If you need more performance, switch to the Gunicorn setup:
1. In Dokploy, change the Dockerfile to `Dockerfile.gunicorn`
2. Set `WORKERS` environment variable (recommended: CPU cores × 2)
3. Redeploy

## ❗ Important Notes

1. **Disk Space**: Downloads are cached - monitor disk usage
2. **API Keys**: Keep them secret and rotate regularly  
3. **CORS**: Update ALLOWED_HOSTS for production security
4. **SSL/TLS**: Always use HTTPS in production
5. **Dependencies**: All unused imports have been removed for smaller image size

## 🆘 Troubleshooting

### Common Issues
- **Health check fails**: Check file permissions and disk space
- **Import errors**: Rebuild image after code changes
- **Out of memory**: Switch to Gunicorn setup or reduce workers
- **Slow downloads**: Check network connectivity and disk I/O

### Debug Commands
```bash
# Check container status
docker ps

# View logs
docker logs nanovideo-api

# Shell into container
docker exec -it nanovideo-api /bin/bash

# Test endpoints
curl -f http://localhost:8000/health
```

### Fixed Issues
- ✅ Removed unused `aiohttp` import that was causing startup failures
- ✅ Corrected Gunicorn startup script options
- ✅ Simplified default deployment to use Sanic directly

Your NanoVideoApi is now ready for production deployment! 🎉

## 🚀 Quick Start Commands

```bash
# Test locally
docker build -t nanovideo-api .
docker run -p 8000:8000 -e API_KEYS=test -e "ALLOWED_HOSTS=*" nanovideo-api

# Test health
curl http://localhost:8000/health

# Test API
curl "http://localhost:8000/?api_key=test"
```
