# Quick Reference Guide

## Local Development (Windows)

### Start the Flask App
```cmd
python app.py
```

Or with WSGI:
```cmd
python wsgi.py
```

Or with Gunicorn:
```cmd
gunicorn -c gunicorn.ini wsgi:app
```

### Test the Application
```cmd
python test_proxy.py
```

### Test Health Endpoint
```cmd
curl http://localhost:5011/health
```

## Production Deployment (Linux)

### Service Management
```bash
# Start
sudo systemctl start flask-proxy

# Stop
sudo systemctl stop flask-proxy

# Restart
sudo systemctl restart flask-proxy

# Status
sudo systemctl status flask-proxy

# Enable on boot
sudo systemctl enable flask-proxy

# Disable on boot
sudo systemctl disable flask-proxy
```

### View Logs
```bash
# Application logs (systemd)
sudo journalctl -u flask-proxy -f

# Application logs (file)
tail -f /var/www/flask-proxy/logs/gateway.log

# Nginx access logs
sudo tail -f /var/log/nginx/api.zvolta.com.access.log

# Nginx error logs
sudo tail -f /var/log/nginx/api.zvolta.com.error.log
```

### Nginx Management
```bash
# Test configuration
sudo nginx -t

# Reload (graceful restart)
sudo systemctl reload nginx

# Restart
sudo systemctl restart nginx

# Status
sudo systemctl status nginx
```

### SSL Certificate (Let's Encrypt)
```bash
# Obtain certificate
sudo certbot --nginx -d api.zvolta.com

# Renew certificates (dry run)
sudo certbot renew --dry-run

# Force renew
sudo certbot renew --force-renewal

# List certificates
sudo certbot certificates
```

## Testing

### Test Local Flask App
```bash
curl http://127.0.0.1:5011/health
```

### Test Through Nginx (HTTP)
```bash
curl http://api.zvolta.com/health
```

### Test Through Nginx (HTTPS)
```bash
curl https://api.zvolta.com/health
```

### Test Proxy Functionality
```bash
# GET request
curl http://api.zvolta.com/

# POST request
curl -X POST http://api.zvolta.com/api/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `.env` | `/var/www/flask-proxy/.env` | Environment variables |
| `app.py` | `/var/www/flask-proxy/app.py` | Flask application |
| `wsgi.py` | `/var/www/flask-proxy/wsgi.py` | WSGI entry point |
| `config.py` | `/var/www/flask-proxy/config.py` | Configuration class |
| `gunicorn.ini` | `/var/www/flask-proxy/gunicorn.ini` | Gunicorn settings |
| `flask-proxy.service` | `/etc/systemd/system/flask-proxy.service` | Systemd service |
| `nginx-api-zvolta.conf` | `/etc/nginx/sites-available/api.zvolta.com` | Nginx config |

## Key Settings

### Port Configuration
- **Flask App**: Port 5011 (localhost only)
- **Nginx**: Port 80 (HTTP), Port 443 (HTTPS)

### Environment Variables
```bash
GATEWAY_HOST=127.0.0.1
GATEWAY_PORT=5011
TARGET_HOST=https://smartswitch.orkofleet.com
PROXY_TIMEOUT=30
```

## Troubleshooting

### Check if Flask is Running
```bash
sudo netstat -tlnp | grep 5011
# or
sudo lsof -i :5011
```

### Check if Nginx is Running
```bash
sudo systemctl status nginx
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

### Test Connection Between Nginx and Flask
```bash
curl http://127.0.0.1:5011/health
```

### View Recent Errors
```bash
# Flask app errors
sudo journalctl -u flask-proxy -n 50 --no-pager

# Nginx errors
sudo tail -n 50 /var/log/nginx/api.zvolta.com.error.log
```

## Update Deployment

```bash
# 1. Stop service
sudo systemctl stop flask-proxy

# 2. Update code
cd /var/www/flask-proxy
sudo -u www-data git pull

# 3. Update dependencies (if needed)
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 4. Start service
sudo systemctl start flask-proxy

# 5. Check status
sudo systemctl status flask-proxy
```

## Monitoring

### Check System Resources
```bash
# CPU and Memory usage
htop

# Disk usage
df -h

# Flask app resource usage
ps aux | grep gunicorn
```

### Check Request Rate
```bash
# Nginx access log (requests per second)
tail -f /var/log/nginx/api.zvolta.com.access.log | pv -l -i 1 -r > /dev/null
```

## Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Check firewall status
sudo ufw status

# Enable firewall
sudo ufw enable
```
