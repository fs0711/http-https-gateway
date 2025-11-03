# Production Deployment Guide with Let's Encrypt SSL

Complete guide for deploying the bidirectional HTTPS/HTTP proxy to production with Let's Encrypt SSL certificates.

## Architecture Overview

```
Internet
    ↓
NGINX Reverse Proxy (Port 443 with Let's Encrypt SSL)
    ↓
Systemd Service (Flask App on Port 5443 with Let's Encrypt SSL)
    ├→ Endpoint A: smartswitch.orkofleet.com
    └→ Endpoint B: api.zvolta.com
```

## Prerequisites

- Ubuntu 20.04 LTS or later (or compatible Linux)
- Domain names pointing to your server:
  - `smartswitch.orkofleet.com`
  - `api.zvolta.com`
- Ports 80 and 443 accessible from internet
- Root or sudo access

## Complete Setup Steps

### Step 1: System Preparation

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    curl

# Create proxy user
sudo useradd -r -s /bin/bash -d /opt/proxy proxy
sudo usermod -aG sudo proxy
```

### Step 2: Get Let's Encrypt Certificates

```bash
# Option A: Single certificate for all domains
sudo certbot certonly --nginx \
    -d smartswitch.orkofleet.com \
    -d www.smartswitch.orkofleet.com \
    -d api.zvolta.com \
    -d www.api.zvolta.com \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email

# Option B: Separate certificates per domain
sudo certbot certonly --nginx -d smartswitch.orkofleet.com
sudo certbot certonly --nginx -d api.zvolta.com
```

Certificates will be located at:
- `/etc/letsencrypt/live/smartswitch.orkofleet.com/`
- `/etc/letsencrypt/live/api.zvolta.com/`

### Step 3: Clone and Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/proxy
sudo chown proxy:proxy /opt/proxy
cd /opt/proxy

# Clone repository
sudo -u proxy git clone https://github.com/fs0711/http-https-gateway.git .

# Create virtual environment
sudo -u proxy python3 -m venv venv
sudo -u proxy ./venv/bin/pip install --upgrade pip
sudo -u proxy ./venv/bin/pip install -r requirements.txt
```

### Step 4: Configure Application

```bash
# Create environment file
sudo tee /opt/proxy/.env > /dev/null <<EOF
FLASK_ENV=production
FLASK_DEBUG=False
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=5443
SSL_ENABLED=True
SSL_CERT_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem
PROXY_ENDPOINT_A=https://smartswitch.orkofleet.com
PROXY_ENDPOINT_B=https://api.zvolta.com
PROXY_TIMEOUT=30
LOG_LEVEL=INFO
LOG_FILE=/var/log/proxy/gateway.log
EOF

# Fix permissions
sudo chown proxy:proxy /opt/proxy/.env
sudo chmod 600 /opt/proxy/.env
```

### Step 5: Setup Certificates Permissions

```bash
# Allow proxy user to read Let's Encrypt certificates
sudo usermod -aG root proxy
sudo chmod 755 /etc/letsencrypt/live/
sudo chmod 755 /etc/letsencrypt/archive/

# Ensure certificate permissions
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 644 /etc/letsencrypt/live/*/cert.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem

# Create renewal hook to restart proxy
sudo mkdir -p /etc/letsencrypt/renewal-hooks/post

sudo tee /etc/letsencrypt/renewal-hooks/post/proxy-restart.sh > /dev/null <<'EOF'
#!/bin/bash
systemctl restart proxy > /dev/null 2>&1
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/post/proxy-restart.sh
```

### Step 6: Create Log Directory

```bash
# Create log directory
sudo mkdir -p /var/log/proxy
sudo chown proxy:proxy /var/log/proxy
sudo chmod 755 /var/log/proxy

# Create log rotation config
sudo tee /etc/logrotate.d/proxy > /dev/null <<'EOF'
/var/log/proxy/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 proxy proxy
    sharedscripts
    postrotate
        systemctl reload proxy > /dev/null 2>&1 || true
    endscript
}
EOF
```

### Step 7: Setup Systemd Service

```bash
# Copy and setup proxy service
sudo cp /opt/proxy/proxy.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/proxy.service
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable proxy
sudo systemctl start proxy

# Verify service is running
sudo systemctl status proxy
```

### Step 8: Configure NGINX as Reverse Proxy

```bash
# Backup original nginx config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Copy Let's Encrypt enabled nginx config
sudo cp /opt/proxy/nginx-letsencrypt.conf /etc/nginx/sites-available/proxy
sudo ln -s /etc/nginx/sites-available/proxy /etc/nginx/sites-enabled/ 2>/dev/null || true

# Disable default site
sudo unlink /etc/nginx/sites-enabled/default 2>/dev/null || true

# Test nginx configuration
sudo nginx -t

# Start and enable nginx
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Step 9: Setup Automatic Certificate Renewal

```bash
# Enable certbot renewal timer (systemd)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal (dry-run)
sudo certbot renew --dry-run

# View renewal status
sudo systemctl status certbot.timer
```

### Step 10: Firewall Configuration

```bash
# Enable firewall
sudo ufw enable

# Open required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for Let's Encrypt renewal)
sudo ufw allow 443/tcp   # HTTPS

# Verify rules
sudo ufw status
```

## Verification

### Test Health Endpoints

```bash
# Test smartswitch domain
curl -v https://smartswitch.orkofleet.com/health

# Test api.zvolta domain
curl -v https://api.zvolta.com/health

# Test with certificate verification
curl -I https://smartswitch.orkofleet.com
curl -I https://api.zvolta.com
```

### Verify SSL Certificates

```bash
# Check certificate details
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -text -noout

# Check expiration dates
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -dates

# List all certificates
sudo certbot certificates

# Verify OCSP status
sudo openssl ocsp -no_nonce -issuer /etc/letsencrypt/live/smartswitch.orkofleet.com/chain.pem \
    -cert /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem \
    -url http://ocsp.int-x3.letsencrypt.org
```

### Check Services Status

```bash
# Proxy service
sudo systemctl status proxy

# NGINX service
sudo systemctl status nginx

# View logs
sudo journalctl -u proxy -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/proxy/gateway.log
```

## Monitoring and Maintenance

### Daily Monitoring

```bash
# Check all services
sudo systemctl status proxy nginx

# Monitor logs
sudo journalctl -u proxy -n 50
sudo tail -f /var/log/nginx/error.log

# Check disk usage
sudo du -sh /var/log/proxy/ /var/log/nginx/
```

### Certificate Renewal Monitoring

```bash
# View renewal log
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Check next renewal date
sudo certbot certificates

# Manual renewal (can be done anytime)
sudo certbot renew

# Force renewal (useful for testing)
sudo certbot renew --force-renewal
```

### Performance Monitoring

```bash
# Monitor application performance
ps aux | grep python

# Check memory usage
sudo systemctl show proxy -p MemoryCurrent

# Network connections
sudo ss -tlnp | grep -E ':(80|443|5443)'

# Monitor in real-time
watch -n 2 'sudo systemctl status proxy && echo "---" && ps aux | grep app.py'
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status and errors
sudo systemctl status proxy -l

# View full logs
sudo journalctl -u proxy -xe

# Check certificate permissions
ls -la /etc/letsencrypt/live/smartswitch.orkofleet.com/

# Test configuration manually
/opt/proxy/venv/bin/python -c "from config import Config; errors = Config.validate(); print(errors or 'Config OK')"
```

### Certificate Issues

```bash
# Certificate not found
sudo certbot certificates

# Regenerate certificate
sudo certbot renew --force-renewal

# Fix permissions
sudo chown -R root:root /etc/letsencrypt/
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :443
sudo lsof -i :5443
sudo lsof -i :80

# Kill if necessary
sudo kill -9 <PID>
```

### NGINX Configuration Errors

```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# View error log
sudo tail -100 /var/log/nginx/error.log
```

### High Memory Usage

```bash
# Check memory limits
sudo systemctl show proxy -p MemoryLimit

# Edit service limits
sudo systemctl edit proxy

# Add under [Service]:
# MemoryMax=2G
# CPUQuota=50%
```

## Backup and Recovery

### Backup Certificates

```bash
# Backup Let's Encrypt directory
sudo tar -czf /backup/letsencrypt-$(date +%Y%m%d).tar.gz /etc/letsencrypt/

# Backup application directory
sudo tar -czf /backup/proxy-app-$(date +%Y%m%d).tar.gz /opt/proxy/
```

### Restore from Backup

```bash
# Restore certificates
sudo tar -xzf /backup/letsencrypt-20231215.tar.gz -C /

# Restore application
sudo tar -xzf /backup/proxy-app-20231215.tar.gz -C /

# Fix permissions
sudo chown -R proxy:proxy /opt/proxy
sudo systemctl restart proxy
```

## Performance Optimization

### NGINX Optimization

```bash
# Edit /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 2048;
keepalive_timeout 65;
```

### Python/Flask Optimization

```bash
# Use Gunicorn for production (optional)
sudo -u proxy pip install gunicorn

# Update service to use Gunicorn:
# ExecStart=/opt/proxy/venv/bin/gunicorn -w 4 -b 0.0.0.0:5443 --certfile=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem --keyfile=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem app:app
```

## SSL/TLS Best Practices

### Security Headers

The NGINX config includes:
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

### Certificate Auto-Renewal

- Certificates renew automatically 30 days before expiration
- Service automatically restarts after renewal via renewal hook
- No manual intervention required

### Monitoring Certificate Expiration

```bash
# Create alert script
sudo tee /usr/local/bin/check-cert-expiry.sh > /dev/null <<'EOF'
#!/bin/bash
for cert in /etc/letsencrypt/live/*/fullchain.pem; do
    expiry=$(sudo openssl x509 -in $cert -noout -dates | grep notAfter | cut -d= -f2)
    days=$(($(date -d "$expiry" +%s) - $(date +%s) / 86400))
    echo "Certificate: $cert expires in $days days"
done
EOF

# Add to crontab for daily checks
# 0 9 * * * /usr/local/bin/check-cert-expiry.sh | mail -s "Certificate Status" admin@example.com
```

## Production Checklist

- [x] Domain names configured in DNS
- [x] Firewall rules configured (80, 443, 22)
- [x] Let's Encrypt certificates obtained
- [x] Application directory setup
- [x] Virtual environment created
- [x] Configuration file setup
- [x] Certificate permissions configured
- [x] Systemd service installed
- [x] NGINX configured as reverse proxy
- [x] Certificate renewal automation enabled
- [x] Log rotation configured
- [x] Health checks verified
- [x] SSL/TLS certificates verified
- [x] Service autostart enabled
- [x] Monitoring and alerting configured

## Reference URLs

- Let's Encrypt: https://letsencrypt.org
- Certbot Documentation: https://certbot.eff.org
- NGINX SSL Configuration: https://nginx.org/en/docs/http/ngx_http_ssl_module.html
- Flask SSL Configuration: https://flask.palletsprojects.com/en/latest/ssl/
