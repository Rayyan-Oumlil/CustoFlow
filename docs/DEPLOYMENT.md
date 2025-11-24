# 🚀 CustoFlow Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.10+** (3.11 or 3.12 recommended)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Google API Key** (for Gemini API access)

### System Requirements
- **RAM**: Minimum 2GB, Recommended 4GB+
- **CPU**: 2+ cores recommended
- **Storage**: 500MB+ free space
- **Network**: Internet connection for API calls

---

## Local Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd customer-support-agent
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.5-flash-lite
API_HOST=0.0.0.0
API_PORT=8000
APP_NAME=CustoFlow
DEBUG=false
```

### 5. Initialize Data Directories
```bash
# Create data directory if it doesn't exist
mkdir -p data
```

### 6. Start the API Server
```bash
# Option 1: Direct Python
python -m api.server

# Option 2: Uvicorn (with auto-reload)
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start the React Frontend
```bash
# In a new terminal
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### 8. Access the Application
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

---

## Production Deployment

### Option 1: Traditional Server Deployment

#### 1. Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.10 python3-pip python3-venv -y

# Install Nginx (reverse proxy)
sudo apt install nginx -y
```

#### 2. Application Setup
```bash
# Clone repository
git clone <repository-url>
cd customer-support-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
nano .env  # Add your configuration
```

#### 3. Create Systemd Service
Create `/etc/systemd/system/custoflow-api.service`:
```ini
[Unit]
Description=CustoFlow API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/customer-support-agent
Environment="PATH=/path/to/customer-support-agent/venv/bin"
ExecStart=/path/to/customer-support-agent/venv/bin/uvicorn api.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable custoflow-api
sudo systemctl start custoflow-api
sudo systemctl status custoflow-api
```

#### 4. Configure Nginx
Create `/etc/nginx/sites-available/custoflow`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/custoflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: Docker Deployment

#### 1. Build Docker Image
```bash
docker build -t custoflow:latest .
```

#### 2. Run Container
```bash
docker run -d \
  --name custoflow \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your_api_key \
  -v $(pwd)/data:/app/data \
  custoflow:latest
```

#### 3. Docker Compose (Recommended)
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - MODEL_NAME=gemini-2.5-flash-lite
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped
```

Start services:
```bash
docker-compose up -d
```

---

## Environment Configuration

### Required Variables
```env
GOOGLE_API_KEY=your_google_api_key_here
```

### Optional Variables
```env
MODEL_NAME=gemini-2.5-flash-lite          # Gemini model to use
API_HOST=0.0.0.0                         # API server host
API_PORT=8000                            # API server port
APP_NAME=CustoFlow                       # Application name
DEBUG=false                              # Debug mode
GOOGLE_CLOUD_PROJECT=                    # Google Cloud project (optional)
GOOGLE_CLOUD_LOCATION=global             # Google Cloud location
```

### Environment-Specific Configs

#### Development
```env
DEBUG=true
API_PORT=8000
```

#### Production
```env
DEBUG=false
API_PORT=8000
# Add monitoring and logging configs
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics
```

### Logs
```bash
# API logs
tail -f logs/api.log

# Systemd logs
journalctl -u custoflow-api -f

# Docker logs
docker logs -f custoflow
```

### Backup Data
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz
```

### Performance Monitoring
- **Response Times**: Monitor `/metrics` endpoint
- **Error Rates**: Check logs for errors
- **Resource Usage**: Use `htop` or `docker stats`
- **API Health**: Set up monitoring alerts

---

## Troubleshooting

### Common Issues

#### 1. API Not Starting
```bash
# Check if port is in use
netstat -tulpn | grep 8000

# Check logs
tail -f logs/api.log

# Verify environment variables
echo $GOOGLE_API_KEY
```

#### 2. Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify Python version
python --version  # Should be 3.10+
```

#### 3. API Key Issues
```bash
# Verify API key is set
python -c "from config.settings import settings; print(settings.google_api_key[:10])"

# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" https://generativelanguage.googleapis.com/v1/models
```

#### 4. Database/File Issues
```bash
# Check file permissions
ls -la data/

# Fix permissions
chmod 755 data/
chmod 644 data/*.json
```

#### 5. Rate Limiting
- Check rate limiter configuration in `utils/rate_limiter.py`
- Adjust limits if needed
- Monitor `/metrics` for rate limit hits

---

## Security Best Practices

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables or secret management
   - Rotate keys regularly

2. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Limit API access to trusted IPs if needed

3. **Data Security**
   - Encrypt sensitive data at rest
   - Use secure file permissions
   - Regular backups

4. **Application Security**
   - Keep dependencies updated
   - Regular security audits
   - Input validation and sanitization

---

## Scaling Considerations

### Horizontal Scaling
- Run multiple API instances behind a load balancer
- Use shared session storage (Redis)
- Implement distributed caching

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement connection pooling

### Database Scaling
- Migrate from JSON to PostgreSQL/MongoDB
- Implement read replicas
- Use connection pooling

---

## Backup & Recovery

### Automated Backups
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backups/custoflow-$DATE.tar.gz /path/to/data/
# Keep only last 7 days
find /backups -name "custoflow-*.tar.gz" -mtime +7 -delete
```

### Recovery
```bash
# Stop services
systemctl stop custoflow-api

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz -C /path/to/

# Restart services
systemctl start custoflow-api
```

---

*Last Updated: 2025-01-16*
*Version: 1.0*

