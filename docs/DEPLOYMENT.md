# RoadSafeNet Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development Setup

### Quick Start
```bash
# Clone repository
git clone https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System.git
cd AI-IoT-Road-Accident-Detection-Alert-System

# Run setup script
chmod +x setup.sh
./setup.sh

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Start services
python main.py              # Terminal 1: Detection system
python frontend/app.py      # Terminal 2: Web dashboard
python backend/api.py       # Terminal 3: API server
```

## Production Deployment

### 1. Server Requirements

**Minimum:**
- 4 CPU cores
- 8 GB RAM
- 50 GB storage
- Ubuntu 20.04 LTS or higher

**Recommended:**
- 8 CPU cores
- 16 GB RAM (32 GB with GPU)
- 100 GB SSD storage
- NVIDIA GPU (for faster detection)
- Ubuntu 22.04 LTS

### 2. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip
sudo apt install -y nodejs npm
sudo apt install -y postgresql  # Optional: for PostgreSQL instead of SQLite
sudo apt install -y nginx certbot python3-certbot-nginx

# Install NVIDIA drivers (if using GPU)
sudo apt install -y nvidia-driver-525
```

### 3. Application Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash roadsafenet
sudo su - roadsafenet

# Clone and setup
git clone https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System.git
cd AI-IoT-Road-Accident-Detection-Alert-System
./setup.sh

# Configure production environment
nano .env
```

**Production .env settings:**
```bash
# Change these for production!
SECRET_KEY="your-very-secure-secret-key-here"
JWT_SECRET_KEY="your-jwt-secret-key-here"

# Use production-grade database
DATABASE_URL="postgresql://user:password@localhost/roadsafenet"

# Configure all API keys
TELEGRAM_BOT_TOKEN="your-actual-bot-token"
TELEGRAM_CHAT_IDS="actual-chat-ids"
```

### 4. Process Management with Systemd

Create service files:

#### Detection Service
```bash
sudo nano /etc/systemd/system/roadsafenet-detection.service
```

```ini
[Unit]
Description=RoadSafeNet Detection Service
After=network.target

[Service]
Type=simple
User=roadsafenet
WorkingDirectory=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System
Environment="PATH=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/venv/bin"
ExecStart=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### API Service
```bash
sudo nano /etc/systemd/system/roadsafenet-api.service
```

```ini
[Unit]
Description=RoadSafeNet API Service
After=network.target

[Service]
Type=simple
User=roadsafenet
WorkingDirectory=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System
Environment="PATH=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/venv/bin"
ExecStart=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/venv/bin/uvicorn backend.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Dashboard Service
```bash
sudo nano /etc/systemd/system/roadsafenet-dashboard.service
```

```ini
[Unit]
Description=RoadSafeNet Dashboard Service
After=network.target

[Service]
Type=simple
User=roadsafenet
WorkingDirectory=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System
Environment="PATH=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/venv/bin"
ExecStart=/home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/venv/bin/python frontend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable roadsafenet-detection roadsafenet-api roadsafenet-dashboard
sudo systemctl start roadsafenet-detection roadsafenet-api roadsafenet-dashboard

# Check status
sudo systemctl status roadsafenet-*
```

### 5. Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/roadsafenet
```

```nginx
# API Server
server {
    listen 80;
    server_name api.roadsafenet.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Dashboard
server {
    listen 80;
    server_name dashboard.roadsafenet.com;

    location / {
        proxy_pass http://localhost:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Dash
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/roadsafenet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d api.roadsafenet.com -d dashboard.roadsafenet.com
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Prisma
RUN pip install prisma
RUN npm install -g prisma

# Copy application
COPY . .

# Generate Prisma client
RUN prisma generate --schema=database/schema.prisma

# Create directories
RUN mkdir -p logs uploads ai_model/models cache/huggingface

# Expose ports
EXPOSE 8000 8050

# Default command
CMD ["python", "main.py"]
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  detection:
    build: .
    container_name: roadsafenet-detection
    command: python main.py
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./database:/app/database
    env_file:
      - .env
    restart: unless-stopped

  api:
    build: .
    container_name: roadsafenet-api
    command: uvicorn backend.api:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped

  dashboard:
    build: .
    container_name: roadsafenet-dashboard
    command: python frontend/app.py
    ports:
      - "8050:8050"
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
```

Deploy with Docker:
```bash
docker-compose up -d
docker-compose logs -f
```

## Cloud Deployment

### AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.large (or g4dn.xlarge with GPU)
   - Storage: 100 GB
   - Security group: Allow ports 22, 80, 443, 8000, 8050

2. **Setup Application**
   ```bash
   ssh ubuntu@your-ec2-ip
   # Follow production deployment steps
   ```

### Google Cloud Platform

1. **Create Compute Engine Instance**
   - Machine type: n1-standard-4
   - Boot disk: Ubuntu 22.04, 100 GB
   - Firewall: Allow HTTP, HTTPS

2. **Deploy Application**
   ```bash
   gcloud compute ssh your-instance-name
   # Follow production deployment steps
   ```

### Azure

1. **Create Virtual Machine**
   - Size: Standard_D4s_v3
   - OS: Ubuntu 22.04
   - Networking: Allow ports 80, 443

2. **Setup Application**
   ```bash
   ssh azureuser@your-vm-ip
   # Follow production deployment steps
   ```

## Monitoring & Maintenance

### Logging

Monitor logs:
```bash
# Application logs
tail -f logs/roadsafenet.log

# Service logs
sudo journalctl -u roadsafenet-detection -f
sudo journalctl -u roadsafenet-api -f
sudo journalctl -u roadsafenet-dashboard -f
```

### Database Backup

```bash
# Backup SQLite database
cp database/roadsafenet.db database/backup_$(date +%Y%m%d).db

# Automated backup script
cat > /home/roadsafenet/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/roadsafenet/backups"
mkdir -p $BACKUP_DIR
cp /home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/database/roadsafenet.db \
   $BACKUP_DIR/roadsafenet_$(date +%Y%m%d_%H%M%S).db
find $BACKUP_DIR -type f -mtime +30 -delete
EOF

chmod +x /home/roadsafenet/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/roadsafenet/backup.sh
```

### System Updates

```bash
# Update application
cd /home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
prisma generate --schema=database/schema.prisma

# Restart services
sudo systemctl restart roadsafenet-*
```

### Performance Monitoring

Install monitoring tools:
```bash
# Install htop for CPU/memory monitoring
sudo apt install htop

# Install nvidia-smi for GPU monitoring (if applicable)
nvidia-smi

# Application metrics
curl http://localhost:8000/api/health
```

### Security Hardening

```bash
# Enable firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Regular security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u roadsafenet-detection -n 50

# Check permissions
ls -la /home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System

# Verify environment
cat /home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System/.env
```

### High CPU usage
```bash
# Check running processes
htop

# Adjust VIDEO_FRAME_SKIP in .env to process fewer frames
```

### Database errors
```bash
# Reinitialize database
cd /home/roadsafenet/AI-IoT-Road-Accident-Detection-Alert-System
source venv/bin/activate
python database/init_db.py reset
python database/init_db.py
```

## Support

For deployment issues, contact:
- GitHub Issues: https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System/issues
