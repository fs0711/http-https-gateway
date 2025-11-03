# Let's Encrypt Quick Reference

Fast reference for common Let's Encrypt operations for this project.

## One-Time Setup (Production)

```bash
# 1. Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# 2. Get certificates for both domains
sudo certbot certonly --nginx \
    -d smartswitch.orkofleet.com \
    -d api.zvolta.com \
    --email admin@example.com \
    --agree-tos

# 3. Verify certificates obtained
sudo certbot certificates
```

## Configure Application

```bash
# 1. Set environment variables in .env or systemd service
SSL_CERT_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem

# 2. Update systemd service
sudo systemctl edit proxy
# Add renewal hook

# 3. Restart service
sudo systemctl restart proxy
```

## Daily Operations

### Check Certificate Status
```bash
# View all certificates
sudo certbot certificates

# Check specific certificate
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -dates
```

### Renew Certificates
```bash
# Automatic renewal (runs automatically)
sudo systemctl status certbot.timer

# Manual renewal
sudo certbot renew

# Force renewal (for testing)
sudo certbot renew --force-renewal

# Dry-run renewal
sudo certbot renew --dry-run
```

### Check Service Status
```bash
# Application
sudo systemctl status proxy

# NGINX
sudo systemctl status nginx

# Certificate renewal
sudo systemctl status certbot.timer
```

## Troubleshooting

### Certificate Issues
```bash
# Verify certificate
sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem -text -noout

# Fix permissions
sudo chmod 755 /etc/letsencrypt/{live,archive}
sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem
```

### Service Issues
```bash
# Check logs
sudo journalctl -u proxy -n 50

# Check NGINX
sudo nginx -t
sudo systemctl restart nginx

# Check certificate paths in config
grep SSL_CERT /etc/systemd/system/proxy.service
```

### Port Issues
```bash
# Find what's using port 443
sudo lsof -i :443

# Find what's using port 5443
sudo lsof -i :5443
```

## File Locations

```
Certificate Directory:    /etc/letsencrypt/live/
Logs:                     /var/log/letsencrypt/
Application Config:       /opt/proxy/.env
Service Config:           /etc/systemd/system/proxy.service
NGINX Config:             /etc/nginx/sites-available/proxy
Application Logs:         /var/log/proxy/gateway.log
```

## Certificate Details

### Certificate File Types
```
fullchain.pem  → Use this in NGINX and Flask (includes chain)
cert.pem       → Certificate only
chain.pem      → Intermediate certificates
privkey.pem    → Private key (keep secure!)
```

### Renewal Details
- **Renewal Window**: 30 days before expiration
- **Renewal Frequency**: Twice daily (automatic)
- **Renewal Trigger**: Certbot timer (systemd)
- **Manual Trigger**: `sudo certbot renew`

## Testing

### Test Certificate Chain
```bash
curl -v https://smartswitch.orkofleet.com 2>&1 | grep certificate
```

### Test Health Endpoint
```bash
# Local
curl -k https://localhost:5443/health

# Production
curl https://smartswitch.orkofleet.com/health
```

### Test with OpenSSL
```bash
# Connect and verify
openssl s_client -connect smartswitch.orkofleet.com:443

# Check certificate
openssl s_client -showcerts -connect smartswitch.orkofleet.com:443
```

## Common Tasks

### Add New Domain
```bash
# Get new certificate
sudo certbot certonly --nginx -d newdomain.com

# Update NGINX config
sudo nano /etc/nginx/sites-available/proxy
# Add new server block with appropriate certificate

# Restart NGINX
sudo systemctl restart nginx
```

### Renew Before Expiration
```bash
# Check when renewal is scheduled
sudo certbot certificates | grep -A 3 "smartswitch"

# Force immediate renewal
sudo certbot renew --force-renewal

# Verify renewal
sudo systemctl restart proxy
sudo systemctl restart nginx
```

### Monitor Renewal Automatically
```bash
# View renewal logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Check renewal status
sudo systemctl status certbot.timer

# View timer details
sudo systemctl list-timers certbot.timer
```

## Security Commands

### Verify Strong Cipher Suites
```bash
# Test SSL/TLS configuration
curl -v --ciphers 'HIGH:!aNULL:!MD5' https://smartswitch.orkofleet.com
```

### Check HSTS Header
```bash
curl -i https://smartswitch.orkofleet.com 2>/dev/null | grep -i strict-transport
```

### Verify Certificate Chain
```bash
openssl s_client -connect smartswitch.orkofleet.com:443 -showcerts | grep "verify OK"
```

## Emergency Procedures

### Certificate Expiration Warning
```bash
# Immediate renewal
sudo certbot renew --force-renewal

# If renewal fails, check logs
sudo tail -100 /var/log/letsencrypt/letsencrypt.log

# Restart service
sudo systemctl restart proxy nginx
```

### Port 80 Blocked (Can't Renew)
```bash
# Check port 80
sudo lsof -i :80

# Use DNS challenge instead
sudo certbot renew --preferred-challenges dns
```

### Certificate Mismatch
```bash
# Check current certificates in config
grep SSL_CERT /etc/systemd/system/proxy.service

# Check installed certificates
sudo certbot certificates

# Update to correct certificate
sudo systemctl edit proxy
# Update SSL_CERT_PATH and SSL_KEY_PATH

# Restart
sudo systemctl restart proxy
```

## Useful Aliases (Add to ~/.bashrc)

```bash
# Check certificate expiration
alias cert-check='sudo certbot certificates'

# Check renewal logs
alias cert-logs='sudo tail -f /var/log/letsencrypt/letsencrypt.log'

# Renew now
alias cert-renew='sudo certbot renew --force-renewal'

# Check service status
alias proxy-status='sudo systemctl status proxy'

# View proxy logs
alias proxy-logs='sudo journalctl -u proxy -f'
```

## Quick Checklist

Before going to production:
- [ ] Domain DNS configured
- [ ] Ports 80, 443 accessible
- [ ] Certificates obtained with Certbot
- [ ] Environment variables set
- [ ] Application directory created
- [ ] Virtual environment installed
- [ ] Systemd service installed
- [ ] NGINX configured
- [ ] Certificate renewal hook set
- [ ] Health endpoints verified
- [ ] SSL/TLS verified with curl

## Support Resources

- Let's Encrypt: https://letsencrypt.org
- Certbot Docs: https://certbot.eff.org/docs/
- NGINX SSL: https://nginx.org/en/docs/http/ngx_http_ssl_module.html
- OpenSSL: https://www.openssl.org/docs/manmaster/man1/openssl.html

## Need Help?

1. Check documentation files in project
2. View application logs: `sudo journalctl -u proxy -xe`
3. Check certificate logs: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`
4. Verify NGINX: `sudo nginx -t`
5. Test endpoints: `curl -v https://smartswitch.orkofleet.com`
