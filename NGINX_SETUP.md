# Nginx Setup Guide

## Installation

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install nginx
```

### CentOS/RHEL
```bash
sudo yum install nginx
```

### macOS
```bash
brew install nginx
```

## Configuration

### 1. Copy Nginx Config
```bash
# Linux/macOS
sudo cp nginx.conf /etc/nginx/sites-available/proxy.conf
sudo ln -s /etc/nginx/sites-available/proxy.conf /etc/nginx/sites-enabled/

# Or add to main nginx.conf
sudo cat nginx.conf >> /etc/nginx/nginx.conf
```

### 2. Create Certificate Directory
```bash
sudo mkdir -p /etc/nginx/certs
```

### 3. Copy SSL Certificates
```bash
sudo cp certs/server.crt /etc/nginx/certs/
sudo cp certs/server.key /etc/nginx/certs/
sudo chmod 600 /etc/nginx/certs/server.key
```

### 4. Update Hosts File (for testing)
```bash
# /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts (Windows)
127.0.0.1 smartswitch.orkofleet.com
127.0.0.1 api.zvolta.com
```

### 5. Test Configuration
```bash
sudo nginx -t
```

### 6. Start Nginx
```bash
# Linux/macOS
sudo systemctl start nginx
sudo systemctl enable nginx

# macOS (if using Homebrew)
brew services start nginx
```

## Verify Setup

```bash
# Check if Nginx is running
sudo systemctl status nginx

# Test proxy
curl -k https://smartswitch.orkofleet.com/health
curl -k https://api.zvolta.com/health

# View logs
sudo tail -f /var/log/nginx/smartswitch_access.log
sudo tail -f /var/log/nginx/apivolta_access.log
```

## Troubleshooting

### Port Already in Use
```bash
sudo lsof -i :80
sudo lsof -i :443
# Kill process if needed
sudo kill -9 <PID>
```

### Certificate Issues
```bash
# Verify certificate
openssl x509 -in /etc/nginx/certs/server.crt -text -noout

# Check certificate dates
openssl x509 -in /etc/nginx/certs/server.crt -noout -dates
```

### Permission Denied
```bash
# Ensure nginx can read certificates
sudo chown nginx:nginx /etc/nginx/certs/*
sudo chmod 644 /etc/nginx/certs/server.crt
sudo chmod 600 /etc/nginx/certs/server.key
```

### Nginx Not Starting
```bash
# Check for config errors
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log
```

## Run Python App in Background

```bash
# Start Flask app in background
nohup python app.py > app.log 2>&1 &

# Or use screen
screen -S proxy python app.py

# Or use supervisor/systemd for production
```

## Production Tips

1. **Use real SSL certificates** from Let's Encrypt
2. **Configure Nginx user permissions** properly
3. **Set up log rotation** for large logs
4. **Enable Nginx caching** for better performance
5. **Monitor resource usage** and scale as needed
