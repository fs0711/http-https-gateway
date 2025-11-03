# Production Deployment Checklist

Use this checklist to ensure your Let's Encrypt SSL deployment is complete and production-ready.

## Pre-Deployment (Before You Start)

### Domain & DNS
- [ ] Domain name registered (e.g., smartswitch.orkofleet.com)
- [ ] DNS records point to your server IP
- [ ] Domain resolves with `nslookup` or `dig`
- [ ] Secondary domain also points to server (api.zvolta.com)

### Server Access
- [ ] SSH access to server working
- [ ] Sudo access available
- [ ] Root or elevated permissions available
- [ ] Ports 22 (SSH), 80 (HTTP), 443 (HTTPS) are open

### System Requirements
- [ ] Ubuntu 20.04 LTS or later installed
- [ ] 2GB+ RAM available
- [ ] 10GB+ disk space available
- [ ] Python 3.8+ available

## Step 1: System Preparation

- [ ] Run system update: `sudo apt-get update && sudo apt-get upgrade -y`
- [ ] Install required packages (nginx, certbot, python3, git, etc.)
- [ ] Create proxy user: `sudo useradd -r -s /bin/bash proxy`
- [ ] Verify user created: `id proxy`

## Step 2: Get Let's Encrypt Certificates

- [ ] Install Certbot: `sudo apt-get install certbot python3-certbot-nginx`
- [ ] Run certificate command: `sudo certbot certonly --nginx -d domain1 -d domain2`
- [ ] Verify certificates obtained: `sudo certbot certificates`
- [ ] Check certificate files exist: `ls /etc/letsencrypt/live/smartswitch.orkofleet.com/`

### Certificate Files
- [ ] `/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem` exists
- [ ] `/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem` exists
- [ ] `/etc/letsencrypt/live/api.zvolta.com/fullchain.pem` exists
- [ ] `/etc/letsencrypt/live/api.zvolta.com/privkey.pem` exists

## Step 3: Application Setup

- [ ] Create /opt/proxy directory: `sudo mkdir -p /opt/proxy`
- [ ] Clone repository: `sudo git clone https://github.com/fs0711/http-https-gateway.git /opt/proxy`
- [ ] Change ownership: `sudo chown -R proxy:proxy /opt/proxy`
- [ ] Create virtual environment: `sudo -u proxy python3 -m venv /opt/proxy/venv`
- [ ] Install dependencies: `sudo -u proxy ./venv/bin/pip install -r requirements.txt`

### Configuration
- [ ] Create or copy .env file
- [ ] Set `SSL_CERT_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/fullchain.pem`
- [ ] Set `SSL_KEY_PATH=/etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem`
- [ ] Set `PROXY_ENDPOINT_A=https://smartswitch.orkofleet.com`
- [ ] Set `PROXY_ENDPOINT_B=https://api.zvolta.com`
- [ ] Verify .env permissions: `sudo chmod 600 /opt/proxy/.env`

## Step 4: Certificate Permissions

- [ ] Allow proxy user to read certificates
- [ ] Run: `sudo usermod -aG root proxy`
- [ ] Fix permissions:
  - [ ] `sudo chmod 755 /etc/letsencrypt/{live,archive}`
  - [ ] `sudo chmod 644 /etc/letsencrypt/live/*/fullchain.pem`
  - [ ] `sudo chmod 600 /etc/letsencrypt/live/*/privkey.pem`
- [ ] Test read access: `sudo -u proxy test -r /etc/letsencrypt/live/smartswitch.orkofleet.com/privkey.pem && echo "OK"`

## Step 5: Log Directory Setup

- [ ] Create log directory: `sudo mkdir -p /var/log/proxy`
- [ ] Set ownership: `sudo chown proxy:proxy /var/log/proxy`
- [ ] Set permissions: `sudo chmod 755 /var/log/proxy`
- [ ] Create log rotation config in `/etc/logrotate.d/proxy`

## Step 6: Renewal Hook Setup

- [ ] Create renewal hook directory: `sudo mkdir -p /etc/letsencrypt/renewal-hooks/post`
- [ ] Create hook script: `/etc/letsencrypt/renewal-hooks/post/proxy-restart.sh`
- [ ] Make executable: `sudo chmod +x /etc/letsencrypt/renewal-hooks/post/proxy-restart.sh`
- [ ] Test hook: `bash /etc/letsencrypt/renewal-hooks/post/proxy-restart.sh`

## Step 7: Systemd Service

- [ ] Copy proxy.service: `sudo cp /opt/proxy/proxy.service /etc/systemd/system/`
- [ ] Update service file with correct paths
- [ ] Verify service syntax: `sudo systemd-analyze verify proxy.service`
- [ ] Reload systemd: `sudo systemctl daemon-reload`
- [ ] Enable service: `sudo systemctl enable proxy`
- [ ] Start service: `sudo systemctl start proxy`
- [ ] Check status: `sudo systemctl status proxy`

### Service Verification
- [ ] Service is running: `sudo systemctl is-active proxy`
- [ ] Service is enabled: `sudo systemctl is-enabled proxy`
- [ ] Service logs show no errors: `sudo journalctl -u proxy -n 20`

## Step 8: NGINX Configuration

- [ ] Copy nginx config: `sudo cp /opt/proxy/nginx-letsencrypt.conf /etc/nginx/sites-available/proxy`
- [ ] Create symlink: `sudo ln -s /etc/nginx/sites-available/proxy /etc/nginx/sites-enabled/proxy`
- [ ] Disable default site: `sudo unlink /etc/nginx/sites-enabled/default`
- [ ] Test configuration: `sudo nginx -t`
- [ ] Restart NGINX: `sudo systemctl restart nginx`
- [ ] Enable NGINX: `sudo systemctl enable nginx`

### NGINX Verification
- [ ] NGINX is running: `sudo systemctl is-active nginx`
- [ ] Config is valid: `sudo nginx -t` (should say "successful")
- [ ] NGINX logs show no errors: `sudo tail -20 /var/log/nginx/error.log`

## Step 9: Automatic Renewal

- [ ] Enable certbot timer: `sudo systemctl enable certbot.timer`
- [ ] Start certbot timer: `sudo systemctl start certbot.timer`
- [ ] Check timer status: `sudo systemctl status certbot.timer`
- [ ] Test renewal (dry-run): `sudo certbot renew --dry-run`
- [ ] View renewal logs: `sudo tail -20 /var/log/letsencrypt/letsencrypt.log`

## Step 10: Firewall Setup

- [ ] Enable UFW: `sudo ufw enable`
- [ ] Allow SSH: `sudo ufw allow 22/tcp`
- [ ] Allow HTTP: `sudo ufw allow 80/tcp`
- [ ] Allow HTTPS: `sudo ufw allow 443/tcp`
- [ ] Check rules: `sudo ufw status`

## Post-Deployment Testing

### Health Checks
- [ ] Local health check: `curl -k https://localhost:5443/health`
- [ ] Domain A health check: `curl https://smartswitch.orkofleet.com/health`
- [ ] Domain B health check: `curl https://api.zvolta.com/health`

### Certificate Verification
- [ ] Certificate chain: `curl -v https://smartswitch.orkofleet.com 2>&1 | grep certificate`
- [ ] Certificate dates: `sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -dates`
- [ ] OCSP status: Certificate should support OCSP stapling (check in curl -v output)

### Service Status
- [ ] Application service running: `sudo systemctl status proxy`
- [ ] NGINX running: `sudo systemctl status nginx`
- [ ] Renewal timer active: `sudo systemctl status certbot.timer`
- [ ] Ports open: `sudo ss -tlnp | grep -E ':(80|443|5443)'`

### Port Testing
- [ ] Port 80 (HTTP) open: `curl -I http://smartswitch.orkofleet.com`
- [ ] Port 443 (HTTPS) open: `curl -I https://smartswitch.orkofleet.com`
- [ ] Port 5443 (Backend) accessible: `curl -k -I https://localhost:5443`

## Monitoring & Logging

### Log Access
- [ ] Can read application logs: `sudo tail -f /var/log/proxy/gateway.log`
- [ ] Can read NGINX logs: `sudo tail -f /var/log/nginx/smartswitch_access.log`
- [ ] Can read system logs: `sudo journalctl -u proxy -f`
- [ ] Can read renewal logs: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`

### Monitoring Setup
- [ ] Create log rotation config
- [ ] Setup log monitoring (optional)
- [ ] Setup alerts for certificate expiration (optional)
- [ ] Setup metrics collection (optional)

## Security Verification

- [ ] SSL certificate valid: `sudo openssl x509 -in /etc/letsencrypt/live/smartswitch.orkofleet.com/cert.pem -noout -issuer`
- [ ] Issuer is "Let's Encrypt"
- [ ] Certificate chain complete: Check with `openssl s_client -connect smartswitch.orkofleet.com:443`
- [ ] TLS 1.2+ only: Verify in NGINX config
- [ ] Strong ciphers: Verify in NGINX config
- [ ] HSTS header: `curl -I https://smartswitch.orkofleet.com | grep Strict`
- [ ] Security headers present: Check with curl -I

## Backup Setup

- [ ] Create backup directory: `sudo mkdir -p /backup`
- [ ] Backup certificates: `sudo tar -czf /backup/letsencrypt-$(date +%Y%m%d).tar.gz /etc/letsencrypt/`
- [ ] Backup application: `sudo tar -czf /backup/proxy-app-$(date +%Y%m%d).tar.gz /opt/proxy/`
- [ ] Test restore procedure
- [ ] Setup automated backups (cron job)

## Documentation

- [ ] Review PRODUCTION_DEPLOYMENT.md
- [ ] Review LETSENCRYPT_QUICKREF.md
- [ ] Save important commands to a file
- [ ] Document your specific configuration
- [ ] Document your server IP and domain names

## Final Checks

### Critical Items
- [ ] ✅ Certificates are valid and not expired
- [ ] ✅ HTTPS endpoints are responding
- [ ] ✅ Services are running and enabled
- [ ] ✅ Logs show no errors
- [ ] ✅ Ports are open and accessible

### Important Items
- [ ] ✅ Certificate permissions are correct
- [ ] ✅ Renewal is configured
- [ ] ✅ Backups are working
- [ ] ✅ Logs are being rotated
- [ ] ✅ Security headers are set

### Nice-to-Have Items
- [ ] ✅ Monitoring is set up
- [ ] ✅ Alerts are configured
- [ ] ✅ Documentation is complete
- [ ] ✅ Team is trained
- [ ] ✅ Runbooks are created

## Sign-Off

- [ ] Production deployment date: _______________
- [ ] Deployed by: _______________
- [ ] Reviewed by: _______________
- [ ] Notes:
  ```
  _______________________________________________
  _______________________________________________
  _______________________________________________
  ```

## Post-Deployment Maintenance (Monthly)

- [ ] Check certificate expiration: `sudo certbot certificates`
- [ ] Review logs for errors: `sudo tail -100 /var/log/letsencrypt/letsencrypt.log`
- [ ] Test renewal: `sudo certbot renew --dry-run`
- [ ] Review service status: `sudo systemctl status proxy nginx certbot.timer`
- [ ] Check disk space: `df -h`
- [ ] Verify backups are working

## Emergency Contact

In case of issues:
1. Check: LETSENCRYPT_QUICKREF.md
2. Review: Troubleshooting sections in documentation
3. Check logs: See "Monitoring & Logging" section above
4. Emergency commands: See emergency procedures in QUICKREF

---

**Congratulations!** Your production deployment with Let's Encrypt SSL is complete! 🎉
