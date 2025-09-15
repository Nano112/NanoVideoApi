# NanoVideoApi

A lightweight video downloading API built with Sanic and yt-dlp, designed for production deployment with Docker and Dokploy.

## Features

- 🎥 Video downloading from multiple platforms via yt-dlp
- 🚀 High-performance async API with Sanic
- 🐳 Production-ready Docker setup
- 🔒 API key authentication
- 🏥 Health check endpoint for container orchestration
- 📦 File caching and streaming
- 🔧 CORS support

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd NanoVideoApi
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration:
```bash
# Update API keys and other settings
nano .env
```

6. Run the application:
```bash
python src/app.py
```

### Docker Development

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8001`

### Production Deployment

#### Building for Production

```bash
# Build the Docker image
docker build -t nanovideo-api:latest .

# Run the container
docker run -d \
  --name nanovideo-api \
  -p 8000:8000 \
  -e API_KEYS=your-secure-api-key \
  -e ALLOWED_HOSTS=yourdomain.com \
  -v ./downloads:/app/downloads \
  -v ./logs:/app/logs \
  nanovideo-api:latest
```

#### Dokploy Deployment

1. Push your code to a Git repository
2. In Dokploy, create a new application
3. Connect your Git repository
4. Set the following environment variables:
   - `API_KEYS`: Comma-separated secure API keys
   - `ALLOWED_HOSTS`: Your domain(s)
   - `HOST`: 0.0.0.0
   - `PORT`: 8000
   - `WORKERS`: 4 (adjust based on your server)

5. Dokploy will automatically build and deploy using the Dockerfile

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Server host | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |
| `DOWNLOADS_DIR` | Directory for downloaded files | /app/downloads | No |
| `API_KEYS` | Comma-separated API keys | - | Yes |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts for CORS | * | No |
| `WORKERS` | Number of Gunicorn workers | 4 | No |
| `LOG_LEVEL` | Logging level | INFO | No |

## API Endpoints

### Health Check
```
GET /health
```
Returns application health status.

### Download Video Information
```
POST /info
Content-Type: application/json
X-API-Key: your-api-key

{
  "url": "https://example.com/video"
}
```

### Download and Cache Video
```
GET /share?url=https://example.com/video&api_key=your-api-key
```

### Stream Video Download
```
GET /download?url=https://example.com/video&api_key=your-api-key
```
Returns the video file as a stream.

### List Cached Files
```
GET /files?api_key=your-api-key
```

### Get Cached File
```
GET /files/{filename}?api_key=your-api-key
```

## Security Considerations

1. **API Keys**: Always use strong, randomly generated API keys in production
2. **CORS**: Specify exact domains instead of `*` for `ALLOWED_HOSTS` in production
3. **HTTPS**: Deploy behind a reverse proxy (nginx/Traefik) with SSL/TLS
4. **Rate Limiting**: Consider implementing rate limiting for production use
5. **File Size Limits**: Monitor disk usage as downloaded files are cached

## Performance Tuning

### Gunicorn Configuration

The production setup uses Gunicorn with the following optimizations:
- Multiple workers based on CPU cores
- Worker recycling to prevent memory leaks
- Optimized timeouts for video processing
- Async worker class for better concurrency

### Docker Optimizations

- Multi-stage build to reduce image size
- Non-root user for security
- Proper signal handling
- Health checks for container orchestration

## Monitoring and Logging

- Health endpoint: `GET /health`
- Access logs: `/app/logs/access.log`
- Error logs: `/app/logs/error.log`
- Application logs: Structured JSON logs via Sanic

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure the downloads directory is writable
2. **Memory Issues**: Adjust worker count based on available memory
3. **Disk Space**: Monitor downloaded files and implement cleanup if needed
4. **Network Timeouts**: Increase Gunicorn timeout for large video downloads

### Health Check Failures

The health endpoint checks:
- Application uptime
- Downloads directory accessibility
- Basic application functionality

If health checks fail, check:
- File system permissions
- Disk space
- Application logs

## Development

### Adding New Features

1. Create a new branch
2. Add your feature to `src/app.py`
3. Update tests if applicable
4. Update documentation
5. Test with Docker Compose
6. Submit a pull request

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
