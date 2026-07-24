"""
User model for FinWise.
Stores user account information including authentication credentials.
"""
from datetime import datetime
from .base import db


class User(db.Model):
    """User account model."""

    __tablename__ = "users"

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Authentication fields
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile information
    full_name = db.Column(db.String(100), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True, default=None)
    phone = db.Column(db.String(20), nullable=True)
    currency = db.Column(db.String(10), default="INR")

    # Account metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (one user has many transactions, categories, budgets)
    transactions = db.relationship("Transaction", backref="user", lazy=True, cascade="all, delete-orphan")
    categories = db.relationship("Category", backref="user", lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """Convert user object to dictionary for API responses."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "profile_pic": self.profile_pic,
            "phone": self.phone,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"
