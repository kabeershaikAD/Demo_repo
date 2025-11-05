# Deployment Guide

## Overview

This guide covers deploying the Agentic Legal RAG system in various environments, from local development to production deployment.

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space minimum
- **CPU**: 4 cores minimum (8 cores recommended)
- **GPU**: Optional but recommended for better performance

### Software Dependencies

- Python package manager (pip or conda)
- Git for version control
- Docker (optional, for containerized deployment)

## Local Development Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd agentic-legal-rag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env_example.txt .env

# Edit configuration
# Set your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" >> .env
```

### 3. Run the System

```bash
# Run example usage
python example_usage.py

# Or start the API server
python -m uvicorn api.main:app --reload
```

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data vector_db logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build and Run

```bash
# Build the image
docker build -t agentic-legal-rag .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/vector_db:/app/vector_db \
  agentic-legal-rag
```

### 3. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  legal-rag:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./vector_db:/app/vector_db
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - legal-rag
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Production Deployment

### 1. Environment Configuration

Create production environment file:

```bash
# .env.production
OPENAI_API_KEY=your_production_api_key
OPENAI_MODEL=gpt-4
TEMPERATURE=0.1
MAX_TOKENS=2000
VECTOR_DB_TYPE=faiss
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
ENABLE_CITATION_VERIFICATION=true
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### 2. System Service (systemd)

Create service file `/etc/systemd/system/legal-rag.service`:

```ini
[Unit]
Description=Agentic Legal RAG System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/legal-rag
Environment=PATH=/opt/legal-rag/venv/bin
ExecStart=/opt/legal-rag/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable legal-rag
sudo systemctl start legal-rag
sudo systemctl status legal-rag
```

### 3. Nginx Configuration

Create `/etc/nginx/sites-available/legal-rag`:

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

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/legal-rag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance

```bash
# Launch EC2 instance (t3.large or larger)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Clone and run
git clone <repository-url>
cd agentic-legal-rag
docker-compose up -d
```

#### 2. ECS (Elastic Container Service)

Create task definition:

```json
{
  "family": "legal-rag",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "legal-rag",
      "image": "your-account.dkr.ecr.region.amazonaws.com/legal-rag:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/legal-rag",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### 1. Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/legal-rag

# Deploy to Cloud Run
gcloud run deploy legal-rag \
  --image gcr.io/PROJECT-ID/legal-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Azure

#### 1. Container Instances

```bash
# Create resource group
az group create --name legal-rag-rg --location eastus

# Deploy container
az container create \
  --resource-group legal-rag-rg \
  --name legal-rag \
  --image your-registry.azurecr.io/legal-rag:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=your-key
```

## Monitoring and Logging

### 1. Application Logs

```bash
# View logs
sudo journalctl -u legal-rag -f

# Or with Docker
docker logs -f legal-rag-container
```

### 2. Health Monitoring

```bash
# Health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
else
    echo "Service is unhealthy (HTTP $response)"
    # Send alert or restart service
fi
```

### 3. Prometheus Metrics (Optional)

Add to `api/main.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
query_counter = Counter('legal_rag_queries_total', 'Total queries processed')
query_duration = Histogram('legal_rag_query_duration_seconds', 'Query processing time')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security Considerations

### 1. API Security

```python
# Add authentication middleware
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Implement token verification
    if not verify_api_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token.credentials

# Apply to protected endpoints
@app.post("/query")
async def process_query(
    request: QueryRequest,
    token: str = Depends(verify_token)
):
    # ... existing code
```

### 2. Input Validation

```python
# Add rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/query")
@limiter.limit("10/minute")
async def process_query(request: Request, query_request: QueryRequest):
    # ... existing code
```

### 3. Data Protection

```python
# Encrypt sensitive data
from cryptography.fernet import Fernet

def encrypt_data(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
```

## Backup and Recovery

### 1. Data Backup

```bash
#!/bin/bash
# Backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/legal-rag/$DATE"

mkdir -p $BACKUP_DIR

# Backup vector database
cp -r vector_db $BACKUP_DIR/

# Backup configuration
cp .env $BACKUP_DIR/

# Backup logs
cp -r logs $BACKUP_DIR/

# Compress backup
tar -czf "legal-rag-backup-$DATE.tar.gz" -C /backup/legal-rag $DATE

# Upload to cloud storage (optional)
# aws s3 cp legal-rag-backup-$DATE.tar.gz s3://your-backup-bucket/
```

### 2. Recovery

```bash
#!/bin/bash
# Recovery script
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Extract backup
tar -xzf $BACKUP_FILE

# Restore data
cp -r backup/legal-rag/*/vector_db ./
cp backup/legal-rag/*/.env ./

# Restart service
sudo systemctl restart legal-rag
```

## Troubleshooting

### Common Issues

1. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Increase swap if needed
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   sudo netstat -tlnp | grep :8000
   
   # Kill process using port
   sudo kill -9 <PID>
   ```

3. **Model Loading Issues**
   ```bash
   # Check disk space
   df -h
   
   # Clear model cache
   rm -rf ~/.cache/huggingface/
   ```

### Performance Tuning

1. **Optimize Model Loading**
   ```python
   # Use model caching
   model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models')
   ```

2. **Batch Processing**
   ```python
   # Process documents in batches
   batch_size = 10
   for i in range(0, len(documents), batch_size):
       batch = documents[i:i+batch_size]
       await process_batch(batch)
   ```

3. **Connection Pooling**
   ```python
   # Use connection pooling for external APIs
   import httpx
   
   async with httpx.AsyncClient() as client:
       response = await client.post(url, json=data)
   ```

## Maintenance

### Regular Tasks

1. **Log Rotation**
   ```bash
   # Configure logrotate
   sudo nano /etc/logrotate.d/legal-rag
   
   # Add:
   /opt/legal-rag/logs/*.log {
       daily
       missingok
       rotate 30
       compress
       delaycompress
       notifempty
       create 644 www-data www-data
   }
   ```

2. **Model Updates**
   ```bash
   # Update models periodically
   pip install --upgrade sentence-transformers transformers
   ```

3. **Security Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade
   
   # Update Python packages
   pip install --upgrade -r requirements.txt
   ```

This deployment guide provides comprehensive instructions for deploying the Agentic Legal RAG system in various environments. Choose the deployment method that best fits your requirements and infrastructure.
