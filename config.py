"""
Configuration module for the HTTPS to GSM gateway.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Base configuration class with common settings."""

    # Flask settings
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    TESTING = os.getenv("FLASK_TESTING", "False").lower() == "true"
    ENV = os.getenv("FLASK_ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # Server settings
    HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
    PORT = int(os.getenv("GATEWAY_PORT", "5443"))
    WORKERS = int(os.getenv("GATEWAY_WORKERS", "4"))

    # SSL/TLS settings
    SSL_ENABLED = os.getenv("SSL_ENABLED", "True").lower() == "true"
    SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "./certs/server.crt")
    SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "./certs/server.key")
    SSL_VERIFY_CLIENT = os.getenv("SSL_VERIFY_CLIENT", "False").lower() == "true"
    SSL_CA_PATH = os.getenv("SSL_CA_PATH", "./certs/ca.crt")

    # Bidirectional Proxy Configuration (from .env only)
    PROXY_ENDPOINT_A = os.getenv("PROXY_ENDPOINT_A")
    PROXY_ENDPOINT_B = os.getenv("PROXY_ENDPOINT_B")
    PROXY_TIMEOUT = int(os.getenv("PROXY_TIMEOUT", "30"))

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "./logs/gateway.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Request settings
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "1048576"))  # 1MB
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> list:
        """
        Validate critical configuration settings.
        Returns list of validation errors, empty if all valid.
        """
        errors = []

        # Check SSL certificates exist
        if cls.SSL_ENABLED:
            if not os.path.exists(cls.SSL_CERT_PATH):
                errors.append(f"SSL certificate not found: {cls.SSL_CERT_PATH}")
            if not os.path.exists(cls.SSL_KEY_PATH):
                errors.append(f"SSL key not found: {cls.SSL_KEY_PATH}")

        # Check proxy endpoints are configured
        if not cls.PROXY_ENDPOINT_A or not cls.PROXY_ENDPOINT_B:
            errors.append("Both PROXY_ENDPOINT_A and PROXY_ENDPOINT_B must be configured")

        # Check log directory exists or can be created
        log_dir = os.path.dirname(cls.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            try:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory: {e}")

        return errors


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    ENV = "production"
    LOG_LEVEL = "INFO"
    VALIDATE_SSL_CERT = True


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    SSL_ENABLED = False


def get_config() -> Config:
    """
    Return appropriate config based on environment.
    """
    env = os.getenv("FLASK_ENV", "production")
    
    if env == "development":
        return DevelopmentConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return ProductionConfig()
