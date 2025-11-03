from flask import Flask, request, jsonify, Response
from config import Config
import requests
import logging

app = Flask(__name__)
config = Config()

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Target proxy configuration
TARGET_HOST = "https://smartswitch.orkofleet.com"

def proxy_request(endpoint_path, method="GET"):
    """
    Proxy requests from api.zvolta.com to smartswitch.orkofleet.com
    Forwards all headers, query params, and body data
    """
    try:
        # Build target URL
        target_url = f"{TARGET_HOST}{endpoint_path}"
        
        # Get query parameters
        query_params = request.args.to_dict()
        
        # Get request body
        data = None
        json_data = None
        if request.is_json:
            json_data = request.get_json()
        elif request.data:
            data = request.data
        
        # Forward headers (exclude hop-by-hop headers)
        excluded_headers = ['host', 'connection', 'keep-alive', 'proxy-authenticate', 
                           'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade']
        headers = {k: v for k, v in request.headers if k.lower() not in excluded_headers}
        
        logger.info(f"Proxying {method} request: {request.url} -> {target_url}")
        
        # Make the request to target server
        response = requests.request(
            method=method,
            url=target_url,
            params=query_params,
            json=json_data,
            data=data,
            headers=headers,
            timeout=config.PROXY_TIMEOUT,
            verify=True,  # Verify SSL for HTTPS target
            allow_redirects=False  # Don't follow redirects automatically
        )
        
        # Prepare response headers (exclude hop-by-hop headers)
        response_headers = [(k, v) for k, v in response.headers.items() 
                           if k.lower() not in excluded_headers]
        
        logger.info(f"Response from {target_url}: {response.status_code}")
        
        # Return response with same status code, headers, and body
        return Response(
            response.content,
            status=response.status_code,
            headers=response_headers
        )
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error for {target_url}")
        return jsonify({'error': 'Request timeout', 'success': False}), 504
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for {target_url}: {str(e)}")
        return jsonify({'error': 'Connection failed to target server', 'success': False}), 502
    
    except Exception as e:
        logger.error(f"Proxy error for {target_url}: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok', 
        'proxy': f"api.zvolta.com -> {TARGET_HOST}",
        'version': '1.0'
    }), 200

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    """Catch-all proxy endpoint - forwards all requests to target"""
    endpoint = f"/{path}" if path else "/"
    method = request.method
    
    logger.debug(f"Received {method} request for {endpoint}")
    return proxy_request(endpoint, method)

if __name__ == '__main__':
    logger.info(f"Starting Flask proxy server")
    logger.info(f"Target host: {TARGET_HOST}")
    logger.info(f"Listening on {config.HOST}:{config.PORT}")
    
    if config.SSL_ENABLED:
        app.run(
            host=config.HOST,
            port=config.PORT,
            ssl_context=(config.SSL_CERT_PATH, config.SSL_KEY_PATH),
            debug=config.DEBUG
        )
    else:
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
