# Bidirectional HTTPS/HTTP Proxy

A simple, fast bidirectional proxy that forwards requests between two endpoints with mixed protocol support (HTTPS ↔ HTTP).

## Features

- ✅ Bidirectional proxying
- ✅ Mixed HTTP/HTTPS protocol support
- ✅ Generic endpoint forwarding
- ✅ All HTTP methods (GET, POST, PUT, DELETE, PATCH)
- ✅ SSL/TLS with self-signed certificates
- ✅ Simple configuration via `.env`
- ✅ Request logging

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Generate SSL certificates
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -out certs/server.crt -keyout certs/server.key -days 365 -subj "/CN=localhost"

# Run
python app.py
```

## Configuration (`.env`)

```env
FLASK_ENV=development
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=5443
SSL_ENABLED=True
PROXY_ENDPOINT_A=https://smartswitch.orkofleet.com
PROXY_ENDPOINT_B=http://api.zvolta.com
PROXY_TIMEOUT=30
LOG_LEVEL=INFO
LOG_FILE=./logs/gateway.log
```

## How It Works

**Request routing:**
- `https://smartswitch.orkofleet.com/any/endpoint` → `http://api.zvolta.com/any/endpoint`
- `http://api.zvolta.com/any/endpoint` → `https://smartswitch.orkofleet.com/any/endpoint`

**Protocol handling:**
- HTTPS requests get SSL verification
- HTTP requests skip SSL verification
- Automatic protocol conversion

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
