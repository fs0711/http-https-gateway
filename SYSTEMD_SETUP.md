# Systemd Service Setup Guide

## Installation

### 1. Create User and Group
```bash
# Create non-root user for the service
sudo useradd -r -s /bin/bash proxy
sudo usermod -aG proxy proxy
```

### 2. Create Application Directory
```bash
# Create app directory
sudo mkdir -p /opt/proxy
sudo cp -r ./* /opt/proxy/
sudo chown -R proxy:proxy /opt/proxy
sudo chmod 755 /opt/proxy
```

### 3. Create Log Directory
```bash
# Create log directory
sudo mkdir -p /var/log/proxy
sudo chown proxy:proxy /var/log/proxy
sudo chmod 755 /var/log/proxy
```

### 4. Setup Virtual Environment
```bash
cd /opt/proxy
sudo -u proxy python3 -m venv venv
sudo -u proxy ./venv/bin/pip install -r requirements.txt
```

### 5. Setup Let's Encrypt Certificates

For production, use Let's Encrypt instead of self-signed certificates:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificates for both domains
sudo certbot certonly --nginx \
    -d smartswitch.orkofleet.com \
    -d api.zvolta.com \
    --email your-email@example.com \
    --agree-tos

# Allow proxy user to read Let's Encrypt certs
sudo usermod -aG root proxy
sudo chmod 755 /etc/letsencrypt/{live,archive}
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem

# Create renewal hook to restart proxy
sudo mkdir -p /etc/letsencrypt/renewal-hooks/post
sudo tee /etc/letsencrypt/renewal-hooks/post/proxy-restart.sh > /dev/null <<'EOF'
#!/bin/bash
systemctl restart proxy
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/post/proxy-restart.sh

# For development (self-signed), use this instead:
# sudo mkdir -p /opt/proxy/certs
# sudo openssl req -x509 -newkey rsa:2048 -nodes \
#     -out /opt/proxy/certs/server.crt -keyout /opt/proxy/certs/server.key \
#     -days 365 -subj "/CN=localhost"
# sudo chown proxy:proxy /opt/proxy/certs/*
# sudo chmod 600 /opt/proxy/certs/server.key
```

### 6. Copy Service File
```bash
# Copy systemd service file
sudo cp proxy.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/proxy.service

# Reload systemd
sudo systemctl daemon-reload
```

### 7. Update Environment Variables
```bash
# Edit the .env file if using env file instead of systemd
sudo nano /opt/proxy/.env

# Or edit systemd service directly
sudo systemctl edit proxy
```

## Management

### Start Service
```bash
sudo systemctl start proxy
```

### Stop Service
```bash
sudo systemctl stop proxy
```

### Restart Service
```bash
sudo systemctl restart proxy
```

### Enable at Boot
```bash
sudo systemctl enable proxy
```

### Disable at Boot
```bash
sudo systemctl disable proxy
```

### Check Service Status
```bash
sudo systemctl status proxy
```

### View Service Logs
```bash
# View recent logs
sudo journalctl -u proxy -n 50

# Follow logs in real-time
sudo journalctl -u proxy -f

# Filter by priority
sudo journalctl -u proxy -p err
```

### View Application Logs
```bash
sudo tail -f /var/log/proxy/gateway.log
```

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status proxy

# View detailed logs
sudo journalctl -u proxy -xe

# Verify config
sudo -u proxy /opt/proxy/venv/bin/python -c "from config import Config; c = Config(); print('Config OK')"
```

### Permission Denied
```bash
# Fix permissions
sudo chown -R proxy:proxy /opt/proxy
sudo chown -R proxy:proxy /var/log/proxy
sudo chmod 755 /opt/proxy
sudo chmod 755 /var/log/proxy
```

### Port Already in Use
```bash
# Check what's using port 5443
sudo netstat -tlnp | grep 5443

# Kill the process if needed
sudo kill -9 <PID>
```

### SSL Certificate Issues
```bash
# Verify certificate
sudo openssl x509 -in /opt/proxy/certs/server.crt -text -noout

# Check certificate dates
sudo openssl x509 -in /opt/proxy/certs/server.crt -noout -dates

# Regenerate if needed
sudo rm /opt/proxy/certs/server.*
sudo openssl req -x509 -newkey rsa:2048 -nodes \
    -out /opt/proxy/certs/server.crt \
    -keyout /opt/proxy/certs/server.key \
    -days 365 -subj "/CN=proxy.local"
sudo chown proxy:proxy /opt/proxy/certs/*
sudo chmod 600 /opt/proxy/certs/server.key
```

### Out of Memory
```bash
# Check memory usage
sudo systemctl status proxy | grep Memory

# Increase memory limit in service file
sudo systemctl edit proxy
# Add: MemoryLimit=2G
```

### Restart Behavior
```bash
# Service will auto-restart on failure (up to 3 times in 60 seconds)
# Check restart count
sudo systemctl show proxy -p NRestarts

# Reset restart counter
sudo systemctl reset-failed proxy
```

## Production Checklist

- [x] Create non-root user (`proxy`)
- [x] Setup virtual environment
- [x] Generate SSL certificates
- [x] Configure environment variables
- [x] Enable service on boot
- [x] Setup log rotation
- [x] Configure Nginx (if using as reverse proxy)
- [x] Monitor resource usage
- [x] Setup backup for certificates
- [x] Document configuration

## Log Rotation

Create `/etc/logrotate.d/proxy`:

```
/var/log/proxy/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 proxy proxy
    postrotate
        systemctl reload proxy > /dev/null 2>&1 || true
    endscript
}
```

Then enable it:
```bash
sudo logrotate -f /etc/logrotate.d/proxy
```

## Monitoring

### Check Service Health
```bash
# Simple health check
curl -k https://localhost:5443/health

# Continuous monitoring
watch -n 5 'sudo systemctl status proxy'
```

### Alert on Failure
```bash
# Send email on service failure
sudo systemctl edit proxy

# Add under [Service]:
OnFailure=user@notification.service
```
