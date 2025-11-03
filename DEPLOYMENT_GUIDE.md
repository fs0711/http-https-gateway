# Deployment Guide: Flask Proxy with Nginx

This guide walks through deploying the Flask proxy server on a Linux server with Nginx as a reverse proxy.

## Architecture

```
Internet → api.zvolta.com:80/443 → Nginx → Flask App (127.0.0.1:5011) → smartswitch.orkofleet.com
```

## Prerequisites

- Ubuntu/Debian Linux server
- Root or sudo access
- Domain name: `api.zvolta.com` pointing to your server's IP
- Python 3.8+
- Nginx

## Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx git

# Install certbot for SSL (optional but recommended)
sudo apt install -y certbot python3-certbot-nginx
```

## Step 2: Create Application Directory

```bash
# Create application directory
sudo mkdir -p /var/www/flask-proxy
cd /var/www/flask-proxy

# Clone or copy your application files here
# Or use git:
# git clone https://github.com/fs0711/http-https-gateway.git .
```

## Step 3: Setup Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate for now
deactivate
```

## Step 4: Configure Application

```bash
# Copy and edit the .env file
cp .env.example .env  # or use the existing .env
nano .env

# Make sure these settings are correct:
# GATEWAY_HOST=127.0.0.1
# GATEWAY_PORT=5011
# TARGET_HOST=https://smartswitch.orkofleet.com
```

## Step 5: Create Logs Directory

```bash
# Create logs directory
mkdir -p /var/www/flask-proxy/logs

# Set proper permissions
sudo chown -R www-data:www-data /var/www/flask-proxy
sudo chmod -R 755 /var/www/flask-proxy
sudo chmod -R 775 /var/www/flask-proxy/logs
```

## Step 6: Setup Systemd Service

```bash
# Copy the service file
sudo cp flask-proxy.service /etc/systemd/system/

# Edit the service file to update paths
sudo nano /etc/systemd/system/flask-proxy.service

# Make sure to update these paths:
# - WorkingDirectory=/var/www/flask-proxy
# - EnvironmentFile=/var/www/flask-proxy/.env
# - Environment="PATH=/var/www/flask-proxy/venv/bin:..."
# - ExecStart=/var/www/flask-proxy/venv/bin/gunicorn -c gunicorn.ini wsgi:app

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable flask-proxy

# Start the service
sudo systemctl start flask-proxy

# Check status
sudo systemctl status flask-proxy
```

## Step 7: Configure Nginx

```bash
# Copy nginx configuration
sudo cp nginx-api-zvolta.conf /etc/nginx/sites-available/api.zvolta.com

# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/api.zvolta.com /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# If test is successful, reload nginx
sudo systemctl reload nginx
```

## Step 8: Test the Setup

```bash
# Test local Flask app
curl http://127.0.0.1:5011/health

# Test through Nginx
curl http://api.zvolta.com/health

# Test proxy functionality
curl http://api.zvolta.com/
```

## Step 9: Setup SSL with Let's Encrypt (Recommended)

```bash
# Obtain SSL certificate
sudo certbot --nginx -d api.zvolta.com

# Certbot will automatically configure nginx for HTTPS
# Follow the prompts

# Test SSL renewal
sudo certbot renew --dry-run

# SSL certificates will auto-renew via cron/systemd timer
```

## Monitoring and Maintenance

### View Application Logs

```bash
# View Flask app logs
sudo journalctl -u flask-proxy -f

# View Nginx access logs
sudo tail -f /var/log/nginx/api.zvolta.com.access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/api.zvolta.com.error.log

# View application file logs
tail -f /var/www/flask-proxy/logs/gateway.log
```

### Manage the Service

```bash
# Start service
sudo systemctl start flask-proxy

# Stop service
sudo systemctl stop flask-proxy

# Restart service
sudo systemctl restart flask-proxy

# Reload configuration without downtime
sudo systemctl reload flask-proxy

# Check status
sudo systemctl status flask-proxy

# View recent logs
sudo journalctl -u flask-proxy -n 100 --no-pager
```

### Update Application

```bash
# Stop the service
sudo systemctl stop flask-proxy

# Update code (if using git)
cd /var/www/flask-proxy
sudo -u www-data git pull

# Or upload new files manually

# Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Restart service
sudo systemctl start flask-proxy
```

### Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

## Troubleshooting

### Flask App Not Starting

```bash
# Check service status
sudo systemctl status flask-proxy

# View detailed logs
sudo journalctl -u flask-proxy -n 50

# Check if port 5011 is in use
sudo netstat -tlnp | grep 5011

# Test manually
cd /var/www/flask-proxy
source venv/bin/activate
python wsgi.py
# or
gunicorn -c gunicorn.ini wsgi:app
```

### Nginx 502 Bad Gateway

```bash
# Check if Flask app is running
sudo systemctl status flask-proxy

# Check Flask app is listening on correct port
sudo netstat -tlnp | grep 5011

# Check nginx error logs
sudo tail -f /var/log/nginx/api.zvolta.com.error.log

# Verify nginx can connect to Flask
curl http://127.0.0.1:5011/health
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/flask-proxy

# Fix permissions
sudo chmod -R 755 /var/www/flask-proxy
sudo chmod -R 775 /var/www/flask-proxy/logs
```

## Security Best Practices

1. **Firewall Configuration**
   ```bash
   # Allow only HTTP and HTTPS
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

2. **Keep System Updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Monitor Logs Regularly**
   ```bash
   # Set up log rotation if not already configured
   sudo nano /etc/logrotate.d/flask-proxy
   ```

4. **Use Strong SSL Configuration**
   - Use Let's Encrypt for free SSL certificates
   - Enable HSTS headers
   - Use modern TLS protocols only (TLSv1.2+)

5. **Rate Limiting** (add to nginx config if needed)
   ```nginx
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
   limit_req zone=api_limit burst=20 nodelay;
   ```

## Performance Tuning

### Gunicorn Workers

Edit `.env` or `gunicorn.ini`:
```bash
# Rule of thumb: (2 x CPU cores) + 1
GATEWAY_WORKERS=5
```

### Nginx Optimization

Edit `/etc/nginx/nginx.conf`:
```nginx
worker_processes auto;
worker_connections 1024;
```

## Backup

```bash
# Backup application directory
sudo tar -czf flask-proxy-backup-$(date +%Y%m%d).tar.gz /var/www/flask-proxy

# Backup nginx configuration
sudo tar -czf nginx-backup-$(date +%Y%m%d).tar.gz /etc/nginx/sites-available/api.zvolta.com
```

## Support

For issues or questions:
- Check logs: `sudo journalctl -u flask-proxy -f`
- GitHub: https://github.com/fs0711/http-https-gateway
- Test endpoint: http://api.zvolta.com/health
