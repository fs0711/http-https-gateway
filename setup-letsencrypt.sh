#!/bin/bash

# Let's Encrypt Certificate Setup Script for NGINX Proxy
# This script automates the setup of Let's Encrypt SSL certificates for your proxy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN1="smartswitch.orkofleet.com"
DOMAIN2="api.zvolta.com"
CERT_EMAIL="your-email@example.com"  # Change this to your email
NGINX_USER="nginx"  # or "www-data" on Debian/Ubuntu

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Let's Encrypt Certificate Setup${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root${NC}"
   exit 1
fi

# Step 1: Install Certbot
echo -e "${YELLOW}Step 1: Installing Certbot...${NC}"
if command -v certbot &> /dev/null; then
    echo -e "${GREEN}✓ Certbot already installed${NC}"
else
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
            apt-get update
            apt-get install -y certbot python3-certbot-nginx
        elif [[ "$ID" == "centos" || "$ID" == "rhel" ]]; then
            yum install -y certbot python3-certbot-nginx
        else
            echo -e "${RED}Unsupported OS. Please install certbot manually.${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✓ Certbot installed${NC}"
fi
echo ""

# Step 2: Create certbot directory
echo -e "${YELLOW}Step 2: Creating certbot directory...${NC}"
mkdir -p /var/www/certbot
mkdir -p /var/cache/nginx
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 3: Stop NGINX temporarily (if running)
echo -e "${YELLOW}Step 3: Preparing for certificate generation...${NC}"
if systemctl is-active --quiet nginx; then
    echo "Stopping NGINX temporarily..."
    systemctl stop nginx
    NGINX_WAS_RUNNING=true
else
    NGINX_WAS_RUNNING=false
fi
echo -e "${GREEN}✓ Ready${NC}"
echo ""

# Step 4: Get certificates
echo -e "${YELLOW}Step 4: Getting Let's Encrypt certificates...${NC}"
echo "Requesting certificates for: $DOMAIN1, $DOMAIN2"
certbot certonly --standalone \
    -d "$DOMAIN1" \
    -d "www.$DOMAIN1" \
    -d "$DOMAIN2" \
    -d "www.$DOMAIN2" \
    --email "$CERT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Certificates obtained successfully${NC}"
else
    echo -e "${RED}✗ Failed to obtain certificates${NC}"
    exit 1
fi
echo ""

# Step 5: Set permissions
echo -e "${YELLOW}Step 5: Setting proper permissions...${NC}"
chmod 755 /etc/letsencrypt/{live,archive}
chmod 644 /etc/letsencrypt/live/*/cert.pem
chmod 644 /etc/letsencrypt/live/*/fullchain.pem
chmod 600 /etc/letsencrypt/live/*/privkey.pem
chmod 644 /var/cache/nginx/ocsp-stapling.cache 2>/dev/null || true
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# Step 6: Copy updated nginx config
echo -e "${YELLOW}Step 6: Updating NGINX configuration...${NC}"
if [ -f "nginx-letsencrypt.conf" ]; then
    cp nginx-letsencrypt.conf /etc/nginx/sites-available/proxy.conf
    echo -e "${GREEN}✓ NGINX config updated${NC}"
else
    echo -e "${YELLOW}! nginx-letsencrypt.conf not found in current directory${NC}"
    echo "  Please manually update NGINX config with Let's Encrypt certificate paths"
fi
echo ""

# Step 7: Test NGINX config
echo -e "${YELLOW}Step 7: Testing NGINX configuration...${NC}"
if nginx -t &> /dev/null; then
    echo -e "${GREEN}✓ NGINX config is valid${NC}"
else
    echo -e "${RED}✗ NGINX config has errors:${NC}"
    nginx -t
    exit 1
fi
echo ""

# Step 8: Start NGINX
echo -e "${YELLOW}Step 8: Starting NGINX...${NC}"
if [ "$NGINX_WAS_RUNNING" = true ]; then
    systemctl start nginx
    echo -e "${GREEN}✓ NGINX started${NC}"
else
    echo -e "${YELLOW}! NGINX was not running previously${NC}"
    echo "  Start it manually when ready: systemctl start nginx"
fi
echo ""

# Step 9: Setup automatic renewal
echo -e "${YELLOW}Step 9: Setting up automatic renewal...${NC}"
mkdir -p /etc/letsencrypt/renewal-hooks/post

# Create renewal hook script
cat > /etc/letsencrypt/renewal-hooks/post/nginx-restart.sh << 'EOF'
#!/bin/bash
systemctl restart nginx
EOF

chmod +x /etc/letsencrypt/renewal-hooks/post/nginx-restart.sh

# Enable renewal timer (systemd)
if command -v systemctl &> /dev/null; then
    systemctl enable certbot.timer
    systemctl start certbot.timer
    echo -e "${GREEN}✓ Automatic renewal enabled${NC}"
else
    echo -e "${YELLOW}! systemd not found. Set up renewal manually using cron:${NC}"
    echo "  0 3 * * * /usr/bin/certbot renew --post-hook 'systemctl restart nginx' >> /var/log/letsencrypt/renewal.log 2>&1"
fi
echo ""

# Step 10: Verify certificates
echo -e "${YELLOW}Step 10: Verifying certificates...${NC}"
certbot certificates
echo ""

# Summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${GREEN}Certificate Information:${NC}"
echo "  Domain 1: $DOMAIN1"
echo "  Domain 2: $DOMAIN2"
echo "  Certificate Path: /etc/letsencrypt/live/"
echo "  Next Renewal: 30 days before expiration"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "  1. Test your HTTPS endpoints:"
echo "     curl -v https://$DOMAIN1/health"
echo "     curl -v https://$DOMAIN2/health"
echo ""
echo "  2. Check renewal status:"
echo "     certbot certificates"
echo "     certbot renew --dry-run"
echo ""
echo "  3. View renewal logs:"
echo "     tail -f /var/log/letsencrypt/letsencrypt.log"
echo ""
echo "  4. Monitor NGINX:"
echo "     systemctl status nginx"
echo ""
