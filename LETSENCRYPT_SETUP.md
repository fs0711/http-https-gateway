# Let's Encrypt SSL Certificate Setup Guide

This guide covers setting up free, automatically-renewing SSL certificates from Let's Encrypt for your NGINX proxy.

## Prerequisites

- A domain name (e.g., `smartswitch.orkofleet.com`, `api.zvolta.com`)
- Linux/Ubuntu server with NGINX installed
- Root or sudo access
- Ports 80 and 443 accessible from the internet (for certificate validation)

## Installation Methods

### Method 1: Using Certbot (Recommended)

Certbot is the easiest and most automated way to get and renew Let's Encrypt certificates.

#### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**CentOS/RHEL:**
```bash
sudo yum install certbot python3-certbot-nginx
```

**macOS:**
```bash
brew install certbot
```

#### Get Certificates for Both Domains

```bash
# For multiple domains (one command):
sudo certbot certonly --nginx \
  -d smartswitch.orkofleet.com \
  -d api.zvolta.com \
  -d www.smartswitch.orkofleet.com \
  -d www.api.zvolta.com

# Or run separately for each domain:
sudo certbot certonly --nginx -d smartswitch.orkofleet.com
sudo certbot certonly --nginx -d api.zvolta.com
```

The certificates will be stored in:
- `/etc/letsencrypt/live/smartswitch.orkofleet.com/`
- `/etc/letsencrypt/live/api.zvolta.com/`

Each directory contains:
- `fullchain.pem` - Certificate chain
- `privkey.pem` - Private key
- `cert.pem` - Certificate only
- `chain.pem` - Certificate chain

#### Automatic Renewal

Certbot automatically sets up renewal:
```bash
# Check renewal status
sudo certbot renew --dry-run

# View renewal timer (on systemd systems)
sudo systemctl status certbot.timer
```

Certificates automatically renew 30 days before expiration.

### Method 2: Manual Certificate Management

If you prefer manual management:

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate (standalone mode - temporarily stops nginx)
sudo systemctl stop nginx
sudo certbot certonly --standalone -d smartswitch.orkofleet.com -d api.zvolta.com
sudo systemctl start nginx

# Manual renewal (yearly)
sudo certbot renew
```

## NGINX Configuration Update

Update your `nginx.conf` with Let's Encrypt certificate paths.

### For Single Certificate (Multiple Domains)

If you got one certificate for both domains:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name smartswitch.orkofleet.com api.zvolta.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server for smartswitch.orkofleet.com
server {
    listen 443 ssl http2;
    server_name smartswitch.orkofleet.com;

    ssl_certificate /etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem;
    
    # ... rest of configuration
}

# HTTPS server for api.zvolta.com
server {
    listen 443 ssl http2;
    server_name api.zvolta.com;

    ssl_certificate /etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem;
    
    # ... rest of configuration
}
```

### For Separate Certificates (One Per Domain)

```nginx
# HTTPS server for smartswitch.orkofleet.com
server {
    listen 443 ssl http2;
    server_name smartswitch.orkofleet.com;

    ssl_certificate /etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem;
    
    # ... rest of configuration
}

# HTTPS server for api.zvolta.com
server {
    listen 443 ssl http2;
    server_name api.zvolta.com;

    ssl_certificate /etc/letsencrypt/live/api.zvolta.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.zvolta.com/privkey.pem;
    
    # ... rest of configuration
}
```

## Certificate Paths Permissions

Let's Encrypt certificates are typically owned by root. Ensure NGINX can read them:

```bash
# Set proper permissions
sudo chmod 755 /etc/letsencrypt/live/
sudo chmod 755 /etc/letsencrypt/live/*/
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem

# Ensure nginx user can read
sudo chown -R root:root /etc/letsencrypt/
sudo usermod -aG root nginx  # (or www-data on Debian)
```

## Verification

```bash
# Check certificate details
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -text -noout

# Check expiration date
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -dates

# Test NGINX configuration
sudo nginx -t

# Restart NGINX
sudo systemctl restart nginx

# Verify SSL/TLS
curl -v https://smartswitch.orkofleet.com/health
curl -v https://api.zvolta.com/health
```

## Renewal & Maintenance

### Manual Renewal
```bash
# Renew all certificates
sudo certbot renew

# Renew with restart
sudo certbot renew --post-hook "systemctl restart nginx"

# Force renewal (useful for testing)
sudo certbot renew --force-renewal
```

### Monitor Renewal
```bash
# Check renewal logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# View all certificates
sudo certbot certificates
```

## Advanced: Using Certbot Hooks

Automate NGINX restart on renewal:

```bash
sudo certbot certonly --nginx \
  -d smartswitch.orkofleet.com \
  -d api.zvolta.com \
  --post-hook "systemctl restart nginx"
```

Or create a renewal hook script at `/etc/letsencrypt/renewal-hooks/post/nginx-restart.sh`:

```bash
#!/bin/bash
systemctl restart nginx
```

Make it executable:
```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/nginx-restart.sh
```

## Troubleshooting

### Certificate Already Exists
```bash
# If certificate exists, use --expand to add more domains
sudo certbot certonly --nginx --expand \
  -d smartswitch.orkofleet.com \
  -d api.zvolta.com \
  -d www.smartswitch.orkofleet.com
```

### Port 80/443 Already in Use
```bash
# Find process using port
sudo lsof -i :80
sudo lsof -i :443

# Stop the process
sudo kill -9 <PID>
```

### Certificate Renewal Failed
```bash
# Check the renewal log
sudo tail -100 /var/log/letsencrypt/letsencrypt.log

# Check DNS resolution
nslookup smartswitch.orkofleet.com

# Manually test renewal
sudo certbot renew --dry-run -v
```

### NGINX Can't Read Certificate
```bash
# Fix permissions
sudo chown -R root:root /etc/letsencrypt/
sudo chmod 755 /etc/letsencrypt/{live,archive}
sudo chmod 644 /etc/letsencrypt/live/*/cert.pem
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem
```

## Step-by-Step Setup

### 1. Install Certbot
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y
```

### 2. Update NGINX Config
- Replace certificate paths in your NGINX config with Let's Encrypt paths
- Use the provided `nginx-letsencrypt.conf` template

### 3. Get Certificates
```bash
sudo certbot certonly --nginx \
  -d smartswitch.orkofleet.com \
  -d api.zvolta.com \
  -d www.smartswitch.orkofleet.com \
  -d www.api.zvolta.com
```

### 4. Update NGINX
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Verify
```bash
curl -v https://smartswitch.orkofleet.com/health
curl -v https://api.zvolta.com/health
```

### 6. Check Renewal Status
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

## Important Notes

- **DNS Configuration**: Your domains must be properly configured in DNS and point to your server
- **Firewall**: Ports 80 and 443 must be accessible for certificate validation
- **Auto-Renewal**: Certbot automatically renews 30 days before expiration
- **Email Notifications**: Register with an email for renewal reminders
- **Certificate Chain**: Always use `fullchain.pem`, not just `cert.pem`, in NGINX config

## References

- Let's Encrypt: https://letsencrypt.org
- Certbot Documentation: https://certbot.eff.org
- NGINX SSL Guide: https://nginx.org/en/docs/http/ngx_http_ssl_module.html
