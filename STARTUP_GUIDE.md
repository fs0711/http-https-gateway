# Starting the Application - Quick Guide

## Overview

The Flask proxy application can be started in several ways depending on your environment and needs:

1. **Development Mode** - Direct Python execution
2. **Production Mode** - Using WSGI server (Gunicorn)
3. **System Service** - Automated startup with systemd

---

## Method 1: Direct Python Execution (Development)

### Using app.py
```bash
# Linux/Mac
python3 app.py

# Windows
python app.py
```

### Using wsgi.py (Recommended for testing WSGI setup)
```bash
# Linux/Mac
python3 wsgi.py

# Windows
python wsgi.py
```

**When to use:**
- Local development
- Testing changes
- Debugging

**Port:** 5011 (default)  
**Access:** http://localhost:5011

---

## Method 2: Gunicorn (Production - Linux Only)

### Basic Command
```bash
gunicorn wsgi:app
```

### With Configuration File (Recommended)
```bash
gunicorn -c gunicorn.ini wsgi:app
```

### With Command-Line Options
```bash
gunicorn \
  -w 4 \
  -b 127.0.0.1:5011 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
```

### With Virtual Environment
```bash
cd /var/www/flask-proxy
source venv/bin/activate
gunicorn -c gunicorn.ini wsgi:app
```

**When to use:**
- Production deployments
- Behind nginx reverse proxy
- When you need multiple worker processes

**Port:** 5011 (configured in gunicorn.ini)  
**Access:** http://127.0.0.1:5011 (usually accessed through nginx)

---

## Method 3: Systemd Service (Production - Linux)

### Start Service
```bash
sudo systemctl start flask-proxy
```

### Stop Service
```bash
sudo systemctl stop flask-proxy
```

### Restart Service
```bash
sudo systemctl restart flask-proxy
```

### Enable Auto-Start on Boot
```bash
sudo systemctl enable flask-proxy
```

### Check Status
```bash
sudo systemctl status flask-proxy
```

### View Logs
```bash
# Follow logs in real-time
sudo journalctl -u flask-proxy -f

# View last 100 lines
sudo journalctl -u flask-proxy -n 100 --no-pager
```

**When to use:**
- Production servers
- Automatic startup on system boot
- Managed service lifecycle
- Integration with system monitoring

**Port:** 5011  
**Access:** Through nginx at http://api.zvolta.com

---

## Verification

### Check if Application is Running

```bash
# Check port 5011
netstat -tlnp | grep 5011
# or
lsof -i :5011
# or (Windows)
netstat -ano | findstr :5011
```

### Test Health Endpoint

```bash
# Direct access
curl http://127.0.0.1:5011/health

# Through nginx
curl http://api.zvolta.com/health
```

Expected response:
```json
{
  "status": "ok",
  "proxy": "api.zvolta.com -> https://smartswitch.orkofleet.com",
  "version": "1.0"
}
```

---

## Environment Setup

### Windows (Development)

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python wsgi.py
```

### Linux (Production)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test with gunicorn
gunicorn -c gunicorn.ini wsgi:app

# Or setup as systemd service
sudo cp flask-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flask-proxy
sudo systemctl start flask-proxy
```

---

## Configuration

All configuration is done through environment variables in the `.env` file:

```bash
# Server settings
GATEWAY_HOST=127.0.0.1
GATEWAY_PORT=5011
GATEWAY_WORKERS=4

# Proxy settings
TARGET_HOST=https://smartswitch.orkofleet.com
PROXY_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

---

## Comparison Table

| Method | Use Case | Startup | Workers | Auto-Restart | Logs |
|--------|----------|---------|---------|--------------|------|
| `python app.py` | Development | Manual | 1 | No | Console |
| `python wsgi.py` | Dev/Testing | Manual | 1 | No | Console |
| `gunicorn` | Production | Manual | Multiple | No | File/Console |
| `systemd` | Production | Automatic | Multiple | Yes | systemd journal |

---

## Troubleshooting

### Application Won't Start

1. **Check Python version**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Verify dependencies**
   ```bash
   pip list | grep -E "Flask|requests|gunicorn"
   ```

3. **Check port availability**
   ```bash
   netstat -tlnp | grep 5011
   ```

4. **Review logs**
   ```bash
   # If using systemd
   sudo journalctl -u flask-proxy -n 50

   # If running directly
   # Check console output
   ```

### Port Already in Use

```bash
# Find process using port 5011
sudo lsof -i :5011

# Kill the process
sudo kill -9 <PID>

# Or change port in .env
echo "GATEWAY_PORT=5012" >> .env
```

### Module Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Best Practices

### Development
- Use `python wsgi.py` for quick testing
- Enable DEBUG mode: `FLASK_DEBUG=True`
- Use `LOG_LEVEL=DEBUG` for detailed logs

### Production
- Always use Gunicorn with systemd service
- Never use DEBUG mode in production
- Use nginx as reverse proxy
- Enable SSL with Let's Encrypt
- Monitor logs regularly
- Set appropriate worker count (CPU cores × 2 + 1)

---

## Quick Start Commands

### First Time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Test the application
python test_wsgi.py
python test_proxy.py

# Start the application
python wsgi.py
```

### Production Deployment
```bash
# Setup service
sudo cp flask-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flask-proxy
sudo systemctl start flask-proxy

# Verify
sudo systemctl status flask-proxy
curl http://127.0.0.1:5011/health
```

---

For more details, see:
- `DEPLOYMENT_GUIDE.md` - Full deployment instructions
- `QUICK_REFERENCE.md` - Command reference
- `README.md` - Project overview
