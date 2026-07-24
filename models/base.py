"""Base database instance shared across all models."""
from flask_sqlalchemy import SQLAlchemy

# Single SQLAlchemy instance used by all models
db = SQLAlchemy()
