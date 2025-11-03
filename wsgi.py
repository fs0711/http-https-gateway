"""
WSGI entry point for the Flask proxy application.
This file is used by WSGI servers like Gunicorn to run the application.

Usage:
    gunicorn wsgi:app
    gunicorn -c gunicorn.ini wsgi:app
"""

from app import app
from config import Config
import logging

# Configure logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Validate configuration on startup
config_errors = Config.validate()
if config_errors:
    logger.warning("Configuration validation warnings:")
    for error in config_errors:
        logger.warning(f"  - {error}")

logger.info(f"WSGI application initialized")
logger.info(f"Target host: {Config.TARGET_HOST}")
logger.info(f"Proxy timeout: {Config.PROXY_TIMEOUT}s")

# The WSGI application
if __name__ == "__main__":
    # This block is used when running with python wsgi.py (development only)
    logger.info("Starting development server...")
    if Config.SSL_ENABLED:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            ssl_context=(Config.SSL_CERT_PATH, Config.SSL_KEY_PATH),
            debug=Config.DEBUG
        )
    else:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
