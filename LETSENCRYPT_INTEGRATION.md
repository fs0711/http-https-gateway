# Let's Encrypt Integration - Complete Project Guide

This document provides a complete overview of Let's Encrypt integration throughout the entire project.

## Project Structure with Let's Encrypt

```
http-https-gateway/
├── Core Application
│   ├── app.py                      # Flask app (uses Let's Encrypt paths)
│   ├── config.py                   # Configuration (updated with Let's Encrypt paths)
│   └── requirements.txt            # Dependencies
│
├── Production Deployment
│   ├── proxy.service               # Systemd service (uses Let's Encrypt certs)
│   ├── nginx-letsencrypt.conf      # NGINX config with Let's Encrypt support
│   └── setup-letsencrypt.sh        # Automated setup script
│
└── Documentation
    ├── PRODUCTION_DEPLOYMENT.md    # Complete production guide with Let's Encrypt
    ├── LETSENCRYPT_SETUP.md        # Let's Encrypt specific guide
    ├── NGINX_SETUP.md              # NGINX setup guide
    ├── SYSTEMD_SETUP.md            # Systemd service guide
    └── README.md                   # Quick start guide
```

## What's Been Updated

### 1. Configuration (`config.py`)

**Before:**
```python
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "./certs/server.crt")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "./certs/server.key")
```

**After:**
```python
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem")
SSL_CA_PATH = os.getenv("SSL_CA_PATH", "/etc/letsencrypt/live/smartswitch.orkofleet.com/chain.pem")
```

### 2. Systemd Service (`proxy.service`)

**Updated to use Let's Encrypt certificate paths:**
```ini
Environment="SSL_CERT_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem"
Environment="SSL_KEY_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem"
Environment="PROXY_ENDPOINT_B=https://api.zvolta.com"  # Changed from http:// to https://
```

### 3. NGINX Configuration (`nginx-letsencrypt.conf`)

**Key features:**
- Let's Encrypt certificate paths for both domains
- OCSP Stapling support
- Automatic renewal endpoint (`.well-known/acme-challenge/`)
- Enhanced security headers
- HSTS preload support

### 4. New Files Created

1. **`PRODUCTION_DEPLOYMENT.md`** - Complete step-by-step production deployment guide
2. **`LETSENCRYPT_SETUP.md`** - Comprehensive Let's Encrypt certificate guide
3. **`setup-letsencrypt.sh`** - Automated setup script for production

## Quick Integration Summary

### Development Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate self-signed certificates (for development only)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
    -out certs/server.crt \
    -keyout certs/server.key \
    -days 365 \
    -subj "/CN=localhost"

# 3. Run application
python app.py
```

### Production Setup (with Let's Encrypt)

```bash
# 1. Install system dependencies
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx python3.11 python3-venv

# 2. Get Let's Encrypt certificates
sudo certbot certonly --nginx \
    -d smartswitch.orkofleet.com \
    -d api.zvolta.com \
    --email your-email@example.com \
    --agree-tos

# 3. Clone and setup application
sudo mkdir -p /opt/proxy
cd /opt/proxy
sudo git clone https://github.com/fs0711/http-https-gateway.git .

# 4. Create virtual environment
sudo -u proxy python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 5. Setup configuration
sudo cp .env.example .env  # Or create .env with your settings

# 6. Install systemd service
sudo cp proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable proxy
sudo systemctl start proxy

# 7. Configure NGINX
sudo cp nginx-letsencrypt.conf /etc/nginx/sites-available/proxy
sudo ln -s /etc/nginx/sites-available/proxy /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# 8. Setup automatic renewal
sudo systemctl enable certbot.timer
```

## Environment Variables for Let's Encrypt

```env
# Certificate Paths (automatic on production)
SSL_CERT_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem

# For development (fallback)
SSL_CERT_PATH=./certs/server.crt
SSL_KEY_PATH=./certs/server.key

# Proxy endpoints (now using HTTPS)
PROXY_ENDPOINT_A=https://smartswitch.orkofleet.com
PROXY_ENDPOINT_B=https://api.zvolta.com
```

## Key Integration Points

### 1. Flask Application (`app.py`)
- ✅ Loads certificates from `config.py`
- ✅ Supports both self-signed (development) and Let's Encrypt (production)
- ✅ No changes required - fully compatible

### 2. Configuration (`config.py`)
- ✅ Updated default certificate paths to Let's Encrypt locations
- ✅ Validates certificate existence on startup
- ✅ Backward compatible with development certificates

### 3. Systemd Service (`proxy.service`)
- ✅ Runs as non-root `proxy` user
- ✅ Points to Let's Encrypt certificate paths
- ✅ Auto-restarts on certificate renewal
- ✅ Has renewal hook configured

### 4. NGINX Reverse Proxy (`nginx-letsencrypt.conf`)
- ✅ Uses Let's Encrypt certificates for both domains
- ✅ Handles certificate renewal endpoints
- ✅ Implements OCSP Stapling
- ✅ Enhanced security headers

### 5. Automatic Certificate Renewal
- ✅ Renewal hook restarts application after cert update
- ✅ Certbot timer runs renewal check twice daily
- ✅ No manual intervention required

## Certificate File Locations

```
/etc/letsencrypt/live/smartswitch.orkofleet.com/
├── cert.pem                # Certificate only
├── chain.pem               # Chain certificate
├── fullchain.pem           # Full chain (used in NGINX/Flask)
└── privkey.pem             # Private key (used in NGINX/Flask)

/etc/letsencrypt/live/api.zvolta.com/
├── cert.pem
├── chain.pem
├── fullchain.pem
└── privkey.pem
```

## Verification Commands

### Check Certificates

```bash
# List all certificates
sudo certbot certificates

# View certificate details
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -text -noout

# Check expiration
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -dates

# Test renewal (dry-run)
sudo certbot renew --dry-run
```

### Check Service Status

```bash
# Application service
sudo systemctl status proxy

# NGINX service
sudo systemctl status nginx

# Certificate renewal timer
sudo systemctl status certbot.timer
```

### Test Endpoints

```bash
# Health check (local)
curl -k https://localhost:5443/health

# Health check (production)
curl https://smartswitch.orkofleet.com/health
curl https://api.zvolta.com/health

# Verify certificate chain
curl -v https://smartswitch.orkofleet.com 2>&1 | grep -A 5 "certificate chain"
```

## Troubleshooting

### Certificate Not Found

```bash
# Check if certificates exist
ls -la /etc/letsencrypt/live/smartswitch.orkofleet.com/

# If not found, get new certificate
sudo certbot certonly --nginx -d smartswitch.orkofleet.com -d api.zvolta.com
```

### Permission Denied

```bash
# Fix permissions
sudo chmod 755 /etc/letsencrypt/{live,archive}
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem

# Add user to root group
sudo usermod -aG root proxy
```

### Service Won't Start

```bash
# Check service logs
sudo journalctl -u proxy -xe

# Validate configuration
/opt/proxy/venv/bin/python -c "from config import Config; print(Config.validate())"

# Check NGINX config
sudo nginx -t
```

## Security Checklist

- [x] Using Let's Encrypt (free, automated) instead of self-signed
- [x] HTTPS for all endpoints
- [x] Automatic certificate renewal
- [x] HSTS header enabled
- [x] Security headers configured
- [x] TLS 1.2 and 1.3 only
- [x] Strong cipher suites
- [x] OCSP Stapling enabled
- [x] Certificate chain validation
- [x] Renewal hook for service restart
- [x] Non-root user running service
- [x] Proper file permissions

## Next Steps

1. **Review Documentation**
   - Read [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for complete guide
   - Check [LETSENCRYPT_SETUP.md](LETSENCRYPT_SETUP.md) for certificate details

2. **Deploy to Production**
   - Follow the production deployment guide
   - Run `sudo bash setup-letsencrypt.sh` for automated setup

3. **Verify Installation**
   - Test endpoints with curl
   - Check certificate details
   - Verify service logs

4. **Monitor and Maintain**
   - Set up log monitoring
   - Configure alerts for certificate expiration
   - Regular security audits

## References

- Let's Encrypt: https://letsencrypt.org
- Certbot: https://certbot.eff.org
- NGINX SSL: https://nginx.org/en/docs/http/ngx_http_ssl_module.html
- Flask SSL: https://flask.palletsprojects.com/en/latest/ssl/
