from flask import Flask, request, jsonify, Response, render_template_string
from config import Config
import requests
import logging
from datetime import datetime
import json
import sqlite3
import threading
import os

app = Flask(__name__)
config = Config()

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Target proxy configuration
TARGET_HOST = "https://smartswitch.orkofleet.com"

# SQLite database for persistent log storage
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'post_requests.db')
db_lock = threading.Lock()

def init_db():
    """Initialize SQLite database for storing POST request logs"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            payload TEXT,
            headers TEXT NOT NULL,
            remote_addr TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create index for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON post_logs(timestamp DESC)')
    conn.commit()
    conn.close()

def cleanup_old_logs():
    """Keep only the most recent 1000 log entries"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM post_logs 
            WHERE id NOT IN (
                SELECT id FROM post_logs 
                ORDER BY id DESC 
                LIMIT 1000
            )
        ''')
        conn.commit()
        conn.close()

def log_post_request(endpoint_path, payload, headers):
    """Log POST request details to SQLite database"""
    try:
        timestamp = datetime.now().isoformat()
        payload_str = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload) if payload else None
        headers_str = json.dumps(dict(headers))
        remote_addr = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO post_logs (timestamp, endpoint, payload, headers, remote_addr, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, endpoint_path, payload_str, headers_str, remote_addr, user_agent))
            conn.commit()
            conn.close()
        
        # Cleanup old logs asynchronously to maintain 1000 entry limit
        threading.Thread(target=cleanup_old_logs, daemon=True).start()
        
        logger.info(f"Logged POST request to {endpoint_path}")
    except Exception as e:
        logger.error(f"Failed to log POST request: {str(e)}")

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
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-right: 10px;
            }
            .refresh-btn {
                background-color: #4CAF50;
                color: white;
            }
            .refresh-btn:hover {
                background-color: #45a049;
            }
            .delete-btn {
                background-color: #f44336;
                color: white;
            }
            .delete-btn:hover {
                background-color: #da190b;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
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
            
            <div class="button-group">
                <button class="btn refresh-btn" onclick="location.reload()">🔄 Refresh Logs</button>
                <button class="btn delete-btn" onclick="deleteLogs()">🗑️ Delete All Logs</button>
            </div>
            
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
        
        <script>
            function deleteLogs() {
                if (confirm('⚠️ Are you sure you want to delete ALL logged requests?\n\nThis action cannot be undone!')) {
                    fetch('/log/delete', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('✅ All logs have been deleted successfully!');
                            location.reload();
                        } else {
                            alert('❌ Error deleting logs: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('❌ Error: ' + error);
                    });
                }
            }
        </script>
    </body>
    </html>
    '''
    
    # Fetch logs from SQLite database (newest first)
    logs_for_display = []
    total_logs = 0
    
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, endpoint, payload, headers, remote_addr, user_agent
                FROM post_logs
                ORDER BY id DESC
                LIMIT 1000
            ''')
            rows = cursor.fetchall()
            total_logs = cursor.execute('SELECT COUNT(*) FROM post_logs').fetchone()[0]
            conn.close()
        
        for row in rows:
            timestamp, endpoint, payload_str, headers_str, remote_addr, user_agent = row
            
            # Parse and format payload
            try:
                payload = json.loads(payload_str) if payload_str else None
                if isinstance(payload, (dict, list)):
                    payload_formatted = json.dumps(payload, indent=2, ensure_ascii=False)
                else:
                    payload_formatted = str(payload) if payload else "(empty)"
            except:
                payload_formatted = payload_str if payload_str else "(empty)"
            
            # Parse and format headers
            try:
                headers = json.loads(headers_str)
                headers_formatted = json.dumps(headers, indent=2, ensure_ascii=False)
            except:
                headers_formatted = headers_str
            
            logs_for_display.append({
                'timestamp': timestamp,
                'endpoint': endpoint,
                'payload_formatted': payload_formatted,
                'headers_formatted': headers_formatted,
                'remote_addr': remote_addr or 'Unknown',
                'user_agent': user_agent or 'Unknown'
            })
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
    
    return render_template_string(
        html_template,
        logs=logs_for_display,
        total_logs=total_logs,
        target_host=TARGET_HOST
    )

@app.route('/log/delete', methods=['POST'])
def delete_logs():
    """Delete all POST request logs"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM post_logs')
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
        
        logger.info(f"Deleted {deleted_count} log entries")
        return jsonify({'success': True, 'deleted_count': deleted_count}), 200
    
    except Exception as e:
        logger.error(f"Error deleting logs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

# Initialize database on app startup
init_db()

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
