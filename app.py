from flask import Flask, request, jsonify, Response, render_template_string
from config import Config
import requests
import logging
from datetime import datetime
from collections import deque
import json

app = Flask(__name__)
config = Config()

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Target proxy configuration
TARGET_HOST = "https://smartswitch.orkofleet.com"

# In-memory storage for POST request logs (max 1000 entries)
post_request_logs = deque(maxlen=1000)

def log_post_request(endpoint_path, payload, headers):
    """Log POST request details"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint_path,
        'payload': payload,
        'headers': dict(headers),
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    post_request_logs.append(log_entry)
    logger.info(f"Logged POST request to {endpoint_path}")

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
        
        # Log POST requests with their payload
        if method == 'POST':
            payload_to_log = json_data if json_data is not None else (data.decode('utf-8', errors='replace') if data else None)
            log_post_request(endpoint_path, payload_to_log, request.headers)
        
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

@app.route('/log', methods=['GET'])
def view_logs():
    """Display POST request logs"""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>POST Request Logs - api.zvolta.com</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .stats {
                background-color: #e8f5e9;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .log-entry {
                background-color: #fafafa;
                border-left: 4px solid #4CAF50;
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 4px;
            }
            .log-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-weight: bold;
                color: #555;
            }
            .timestamp {
                color: #4CAF50;
            }
            .endpoint {
                color: #2196F3;
                font-size: 1.1em;
                margin: 10px 0;
            }
            .payload {
                background-color: #263238;
                color: #aed581;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                margin: 10px 0;
            }
            pre {
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .headers {
                background-color: #fff3e0;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                font-size: 0.9em;
            }
            .no-logs {
                text-align: center;
                color: #999;
                padding: 40px;
                font-size: 1.2em;
            }
            .refresh-btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-bottom: 20px;
            }
            .refresh-btn:hover {
                background-color: #45a049;
            }
            .meta-info {
                color: #666;
                font-size: 0.9em;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📝 POST Request Logs - api.zvolta.com</h1>
            
            <div class="stats">
                <strong>Total Logged Requests:</strong> {{ total_logs }}
                <br>
                <strong>Max Storage:</strong> 1000 entries (oldest entries auto-removed)
                <br>
                <strong>Target Host:</strong> {{ target_host }}
            </div>
            
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Logs</button>
            
            {% if logs %}
                {% for log in logs %}
                <div class="log-entry">
                    <div class="log-header">
                        <span class="timestamp">⏱️ {{ log.timestamp }}</span>
                        <span class="remote-addr">🌐 {{ log.remote_addr }}</span>
                    </div>
                    <div class="endpoint">📍 Endpoint: <strong>{{ log.endpoint }}</strong></div>
                    <div class="meta-info">👤 User-Agent: {{ log.user_agent }}</div>
                    
                    <h4>📦 Payload:</h4>
                    <div class="payload">
                        <pre>{{ log.payload_formatted }}</pre>
                    </div>
                    
                    <details>
                        <summary style="cursor: pointer; color: #666; margin-top: 10px;">📋 View Headers</summary>
                        <div class="headers">
                            <pre>{{ log.headers_formatted }}</pre>
                        </div>
                    </details>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-logs">
                    ℹ️ No POST requests logged yet.
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    
    # Prepare logs for display (reverse to show newest first)
    logs_for_display = []
    for log in reversed(post_request_logs):
        # Format payload for display
        payload = log['payload']
        if isinstance(payload, dict) or isinstance(payload, list):
            payload_formatted = json.dumps(payload, indent=2, ensure_ascii=False)
        elif payload is not None:
            payload_formatted = str(payload)
        else:
            payload_formatted = "(empty)"
        
        # Format headers
        headers_formatted = json.dumps(log['headers'], indent=2, ensure_ascii=False)
        
        logs_for_display.append({
            'timestamp': log['timestamp'],
            'endpoint': log['endpoint'],
            'payload_formatted': payload_formatted,
            'headers_formatted': headers_formatted,
            'remote_addr': log['remote_addr'],
            'user_agent': log['user_agent']
        })
    
    return render_template_string(
        html_template,
        logs=logs_for_display,
        total_logs=len(post_request_logs),
        target_host=TARGET_HOST
    )

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
