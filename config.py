"""
Configuration settings for FinWise application.
Loads environment variables and sets up app configuration.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # Flask secret key for session management
    SECRET_KEY = os.environ.get("SECRET_KEY", "finwise-secret-key-change-in-production")

    # Database configuration – use SQLite by default.
    # If FINWISE_DATABASE_URL is explicitly set, use that (supports MySQL/Postgres in production).
    # We intentionally avoid the generic DATABASE_URL env var since Replit may inject a
    # platform-managed Postgres URL that we don't want this project to use.
    _db_url = os.environ.get("FINWISE_DATABASE_URL", "sqlite:///finwise.db")
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "finwise-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Google OAuth (Sign in with Google)
    # Get your Client ID from: https://console.cloud.google.com/apis/credentials
    # Set the GOOGLE_CLIENT_ID environment secret in Replit Secrets panel.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

    # CORS settings
    CORS_ORIGINS = ["*"]

    # ML model paths
    ML_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml", "models")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


# Select configuration based on environment
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

# Default to development
AppConfig = config_map.get(os.environ.get("FLASK_ENV", "development"), DevelopmentConfig)
