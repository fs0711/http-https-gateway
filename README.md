# Bidirectional HTTPS/HTTP Proxy

A simple, fast bidirectional proxy that forwards requests between two endpoints with mixed protocol support (HTTPS ↔ HTTP).

## Features

- ✅ **Bidirectional proxying** - Request routing between endpoints
- ✅ **Mixed HTTPS/HTTP support** - Protocol conversion
- ✅ **Let's Encrypt SSL** - Free, automatic certificate renewal
- ✅ **All HTTP methods** - GET, POST, PUT, DELETE, PATCH
- ✅ **NGINX reverse proxy** - Industry-standard web server
- ✅ **Systemd service** - Production-ready deployment
- ✅ **Request logging** - Comprehensive access and error logs
- ✅ **Security headers** - HSTS, CSP, X-Frame-Options, etc.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# For development (with self-signed certificates):
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -out certs/server.crt -keyout certs/server.key -days 365 -subj "/CN=localhost"

# Run locally
python app.py
```

### Production Deployment

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for complete production setup with Let's Encrypt.

Quick summary:
```bash
# 1. Get Let's Encrypt certificates
sudo certbot certonly --nginx -d smartswitch.orkofleet.com -d api.zvolta.com

# 2. Deploy with systemd
sudo bash setup-letsencrypt.sh

# 3. Configure NGINX
sudo cp nginx-letsencrypt.conf /etc/nginx/sites-available/proxy
```

## Configuration

### Environment Variables (`.env`)

```env
# Flask settings
FLASK_ENV=production              # development, testing, production
FLASK_DEBUG=False                 # Enable Flask debug mode
GATEWAY_HOST=0.0.0.0              # Bind address
GATEWAY_PORT=5443                 # Port to listen on

# SSL/TLS with Let's Encrypt
SSL_ENABLED=True                  # Enable SSL
SSL_CERT_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem

# Proxy endpoints
PROXY_ENDPOINT_A=https://smartswitch.orkofleet.com
PROXY_ENDPOINT_B=https://api.zvolta.com
PROXY_TIMEOUT=30                  # Request timeout in seconds

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/var/log/proxy/gateway.log
```

## How It Works

```
Client Request to smartswitch.orkofleet.com
        ↓
   NGINX (Port 443)
        ↓
   Flask App (Port 5443)
        ↓
Proxy to api.zvolta.com
        ↓
Response back through Flask + NGINX
```

## SSL/TLS with Let's Encrypt

### Automatic Certificate Renewal

Certificates are automatically renewed 30 days before expiration:

```bash
# Check renewal status
sudo certbot certificates

# Renew manually (if needed)
sudo certbot renew

# Monitor renewal logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Certificate Details

```bash
# View certificate
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -text -noout

# Check expiration
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -dates
```

## Testing

```bash
# Health check
curl -k https://localhost:5443/health

# Forward any request
curl -k -X POST https://localhost:5443/api/test \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

## Files

- `app.py` - Main proxy application
- `config.py` - Configuration from environment variables
- `.env` - Configuration file
- `requirements.txt` - Python dependencies
- `setup.sh` - Setup script for Unix/Linux/macOS
