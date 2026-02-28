# TrueFace AI - Deployment Guide

## Production Deployment

This guide covers deploying TrueFace AI to a production environment.

## Prerequisites

- **Server**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **Domain**: Optional (for HTTPS)

## Deployment Options

### Option 1: Local Server Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies for OpenCV and dlib
sudo apt install build-essential cmake -y
sudo apt install libopencv-dev python3-opencv -y
sudo apt install libboost-all-dev -y
```

#### 2. Application Setup

```bash
# Clone or copy project to server
cd /opt
sudo mkdir trueface-ai
sudo chown $USER:$USER trueface-ai
cd trueface-ai

# Copy all project files here

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn

# Initialize database
python backend/init_db.py
```

#### 3. Configure Gunicorn

Create `gunicorn_config.py`:

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 300  # Increased for video processing
keepalive = 2

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
loglevel = 'info'

# Process naming
proc_name = 'trueface-ai'

# Server mechanics
daemon = False
pidfile = 'trueface-ai.pid'
```

Create logs directory:
```bash
mkdir logs
```

#### 4. Create Systemd Service

Create `/etc/systemd/system/trueface-ai.service`:

```ini
[Unit]
Description=TrueFace AI Face Recognition System
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/trueface-ai
Environment="PATH=/opt/trueface-ai/venv/bin"
ExecStart=/opt/trueface-ai/venv/bin/gunicorn -c gunicorn_config.py backend.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trueface-ai
sudo systemctl start trueface-ai
sudo systemctl status trueface-ai
```

#### 5. Configure Nginx Reverse Proxy

Install Nginx:
```bash
sudo apt install nginx -y
```

Create `/etc/nginx/sites-available/trueface-ai`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increased timeouts for video processing
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/trueface-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Setup SSL/HTTPS (Optional but Recommended)

Install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
```

Get SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopencv-dev \
    python3-opencv \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p backend/uploads backend/temp face_database/images face_database/embeddings

# Initialize database
RUN python backend/init_db.py

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "--timeout", "300", "backend.app:app"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  trueface-ai:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./face_database:/app/face_database
      - ./backend/uploads:/app/backend/uploads
      - ./backend/temp:/app/backend/temp
      - ./trueface.db:/app/trueface.db
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

#### 3. Build and Run

```bash
# Build image
docker-compose build

# Run container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

### Option 3: Cloud Deployment (AWS/Azure/GCP)

#### AWS EC2 Deployment

1. **Launch EC2 Instance**:
   - Instance type: t3.medium or larger
   - OS: Ubuntu 20.04 LTS
   - Storage: 20GB EBS volume
   - Security group: Allow ports 80, 443, 22

2. **Connect and Setup**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Follow Local Server Deployment steps above**

4. **Configure Security**:
   - Use AWS Security Groups
   - Enable CloudWatch monitoring
   - Setup auto-scaling (optional)

#### Azure App Service Deployment

1. **Create App Service**:
   - Runtime: Python 3.10
   - OS: Linux
   - Pricing tier: B2 or higher

2. **Deploy using Azure CLI**:
   ```bash
   az webapp up --name trueface-ai --resource-group myResourceGroup
   ```

3. **Configure Application Settings**:
   - Add environment variables
   - Increase timeout settings
   - Configure storage for uploads

## Production Configuration

### 1. Update config.py

```python
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Use environment variables for sensitive data
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database (consider PostgreSQL for production)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "trueface.db"}'
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS (restrict to your domain)
    CORS_ORIGINS = [
        'https://your-domain.com',
        'https://www.your-domain.com'
    ]
```

### 2. Environment Variables

Create `.env` file (never commit to git):

```bash
FLASK_ENV=production
SECRET_KEY=your-very-secret-key-here
DATABASE_URL=sqlite:///trueface.db
```

### 3. Security Hardening

1. **Firewall Configuration**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **File Permissions**:
   ```bash
   chmod 600 .env
   chmod 755 backend/
   chmod 700 face_database/
   ```

3. **Regular Updates**:
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Python packages
   pip install --upgrade -r requirements.txt
   ```

## Performance Optimization

### 1. Enable GPU Acceleration (Optional)

If you have NVIDIA GPU:

```bash
# Install CUDA toolkit
# Follow: https://developer.nvidia.com/cuda-downloads

# Install GPU-enabled TensorFlow
pip install tensorflow-gpu

# Update config.py
USE_GPU = True
```

### 2. Caching

Consider adding Redis for caching:

```bash
pip install redis flask-caching
```

### 3. Database Optimization

For high traffic, migrate to PostgreSQL:

```bash
pip install psycopg2-binary

# Update DATABASE_URL in config
DATABASE_URL=postgresql://user:password@localhost/trueface
```

## Monitoring and Maintenance

### 1. Application Monitoring

```bash
# View application logs
sudo journalctl -u trueface-ai -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. System Monitoring

Install monitoring tools:
```bash
sudo apt install htop iotop -y
```

### 3. Backup Strategy

Create backup script `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/trueface-ai"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp trueface.db $BACKUP_DIR/trueface_$DATE.db

# Backup face database
tar -czf $BACKUP_DIR/faces_$DATE.tar.gz face_database/

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

Schedule with cron:
```bash
crontab -e
# Add: 0 2 * * * /opt/trueface-ai/backup.sh
```

## Troubleshooting Production Issues

### High Memory Usage
- Reduce number of Gunicorn workers
- Increase server RAM
- Implement request queuing

### Slow Video Processing
- Increase `VIDEO_FRAME_SKIP`
- Use GPU acceleration
- Implement async processing with Celery

### Database Locks
- Migrate to PostgreSQL
- Implement connection pooling
- Use read replicas

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer Setup**:
   - Use Nginx or HAProxy
   - Distribute requests across multiple servers
   - Implement session affinity

2. **Shared Storage**:
   - Use NFS or cloud storage (S3, Azure Blob)
   - Centralize face database
   - Sync uploaded files

### Vertical Scaling

1. **Increase Resources**:
   - More CPU cores
   - More RAM
   - Faster storage (SSD)

2. **Optimize Code**:
   - Profile bottlenecks
   - Implement caching
   - Use async processing

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] Strong SECRET_KEY configured
- [ ] Firewall configured
- [ ] Regular security updates
- [ ] File permissions set correctly
- [ ] Database access restricted
- [ ] CORS properly configured
- [ ] Input validation enabled
- [ ] Rate limiting implemented
- [ ] Monitoring and logging active
- [ ] Backup strategy in place
- [ ] Environment variables secured

## Support and Maintenance

### Regular Tasks

**Daily**:
- Monitor application logs
- Check system resources
- Verify backups

**Weekly**:
- Review detection accuracy
- Clean temporary files
- Update dependencies

**Monthly**:
- Security updates
- Performance review
- Database optimization

---

**TrueFace AI** - Production Deployment Guide 2026
