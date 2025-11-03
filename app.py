from flask import Flask, request, jsonify
from config import Config
import requests
import logging

app = Flask(__name__)
config = Config()

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

def get_target_url(source_url):
    """Determine target endpoint based on source"""
    if config.PROXY_ENDPOINT_A in source_url:
        return config.PROXY_ENDPOINT_B
    elif config.PROXY_ENDPOINT_B in source_url:
        return config.PROXY_ENDPOINT_A
    else:
        return config.PROXY_ENDPOINT_B

def should_verify_ssl(target_url):
    """Determine if SSL verification is needed based on target URL"""
    return target_url.startswith("https://")

def proxy_request(endpoint_path, method="POST"):
    """Generic proxy request handler with mixed protocol support"""
    try:
        referer = request.headers.get('Referer', '')
        target_base = get_target_url(referer)
        target_url = f"{target_base}{endpoint_path}"
        
        # Determine if SSL verification is needed
        verify_ssl = should_verify_ssl(target_url)
        
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.data:
            data = request.data
        
        headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'connection']}
        
        logger.info(f"Proxying {method} request to {target_url} (SSL verify: {verify_ssl})")
        
        response = requests.request(
            method=method,
            url=target_url,
            json=data if isinstance(data, dict) else None,
            data=data if isinstance(data, str) else None,
            headers=headers,
            timeout=config.PROXY_TIMEOUT,
            verify=verify_ssl  # Use intelligent SSL verification
        )
        
        return jsonify(response.json() if response.headers.get('content-type') == 'application/json' else response.text), response.status_code
    
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'proxy': f"{config.PROXY_ENDPOINT_A} <-> {config.PROXY_ENDPOINT_B}"}), 200

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """Catch-all proxy endpoint"""
    endpoint = f"/{path}" if path else "/"
    method = request.method
    
    logger.info(f"Received {method} {endpoint}")
    return proxy_request(endpoint, method)

if __name__ == '__main__':
    logger.info(f"Starting bidirectional proxy")
    logger.info(f"Endpoint A: {config.PROXY_ENDPOINT_A}")
    logger.info(f"Endpoint B: {config.PROXY_ENDPOINT_B}")
    
    if config.SSL_ENABLED:
        app.run(
            host=config.HOST,
            port=config.PORT,
            ssl_context=(config.SSL_CERT_PATH, config.SSL_KEY_PATH),
            debug=config.DEBUG
        )
    else:
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
