# Deployment Guide for NanoVideoApi

## 🚀 Quick Deployment Summary

Your NanoVideoApi is now production-ready! Here's what has been set up:

## ✅ What's Been Created

### Core Files
- `Dockerfile` - Multi-stage production Docker build
- `docker-compose.yml` - Local testing setup
- `start.sh` - Production startup script with Gunicorn
- `.dockerignore` - Optimized build context
- `.env.example` - Environment configuration template
- `README.md` - Complete documentation

### Application Updates
- Added `/health` endpoint for container health checks
- Updated logging and error handling
- Production-ready Gunicorn configuration
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
     WORKERS=4
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
  -e ALLOWED_HOSTS=* \
  nanovideo-api
```

## 🔧 Configuration Options

### Environment Variables
| Variable | Production Example | Description |
|----------|-------------------|-------------|
| `API_KEYS` | `key1,key2,key3` | Secure API keys |
| `ALLOWED_HOSTS` | `api.yourdomain.com` | Specific domains for CORS |
| `WORKERS` | `4` | Gunicorn workers (CPU cores × 2) |
| `PORT` | `8000` | Application port |

### Performance Tuning
- **Workers**: Set to `(CPU cores × 2) + 1`
- **Memory**: ~512MB per worker recommended
- **Storage**: Monitor downloads directory growth

## 📊 Monitoring

### Health Checks
- Endpoint: `GET /health`
- Docker health check: Built-in every 30 seconds
- Returns application uptime and system status

### Logs
- Access logs: `/app/logs/access.log`
- Error logs: `/app/logs/error.log`
- Application logs: stdout/stderr

## 🔒 Security Checklist

- [x] Non-root user in container
- [x] API key authentication required
- [ ] Update ALLOWED_HOSTS for production (replace `*`)
- [ ] Use secure, random API keys
- [ ] Deploy behind HTTPS reverse proxy
- [ ] Consider implementing rate limiting

## 🎯 API Endpoints

Once deployed, your API will have these endpoints:

```bash
# Health check (no auth required)
GET /health

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

### Scaling
- Increase `WORKERS` environment variable
- Monitor CPU and memory usage
- Consider horizontal scaling for high traffic

## ❗ Important Notes

1. **Disk Space**: Downloads are cached - monitor disk usage
2. **API Keys**: Keep them secret and rotate regularly  
3. **CORS**: Update ALLOWED_HOSTS for production security
4. **SSL/TLS**: Always use HTTPS in production
5. **Backups**: Consider backing up cached files if needed

## 🆘 Troubleshooting

### Common Issues
- Health check fails: Check file permissions and disk space
- Out of memory: Reduce worker count or increase server memory
- Slow downloads: Check network connectivity and disk I/O

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

Your NanoVideoApi is now ready for production deployment! 🎉
