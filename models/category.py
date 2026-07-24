"""
Category model for FinWise.
Stores expense and income categories (default + custom user-defined).
"""
from datetime import datetime
from .base import db


class Category(db.Model):
    """Transaction category model."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Owner (null means it's a global default category)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Category details
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    icon = db.Column(db.String(50), default="fa-tag")
    color = db.Column(db.String(20), default="#6366f1")

    # Is this a default system category or user-created?
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to transactions
    transactions = db.relationship("Transaction", backref="category", lazy=True)

    def to_dict(self):
        """Convert category to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "icon": self.icon,
            "color": self.color,
            "is_default": self.is_default,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Category {self.name}>"


# Default categories to seed the database on first run
DEFAULT_CATEGORIES = [
    # Expense categories
    {"name": "Food & Dining", "type": "expense", "icon": "fa-utensils", "color": "#f97316"},
    {"name": "Shopping", "type": "expense", "icon": "fa-shopping-bag", "color": "#ec4899"},
    {"name": "Travel", "type": "expense", "icon": "fa-plane", "color": "#06b6d4"},
    {"name": "Bills & Utilities", "type": "expense", "icon": "fa-file-invoice", "color": "#ef4444"},
    {"name": "Medical", "type": "expense", "icon": "fa-hospital", "color": "#10b981"},
    {"name": "Education", "type": "expense", "icon": "fa-graduation-cap", "color": "#8b5cf6"},
    {"name": "Investment", "type": "expense", "icon": "fa-chart-line", "color": "#3b82f6"},
    {"name": "Entertainment", "type": "expense", "icon": "fa-film", "color": "#f59e0b"},
    {"name": "Fuel", "type": "expense", "icon": "fa-gas-pump", "color": "#64748b"},
    {"name": "Others", "type": "expense", "icon": "fa-ellipsis-h", "color": "#94a3b8"},
    # Income categories
    {"name": "Salary", "type": "income", "icon": "fa-briefcase", "color": "#22c55e"},
    {"name": "Freelance", "type": "income", "icon": "fa-laptop", "color": "#a855f7"},
    {"name": "Business", "type": "income", "icon": "fa-building", "color": "#0ea5e9"},
    {"name": "Investment Returns", "type": "income", "icon": "fa-piggy-bank", "color": "#14b8a6"},
    {"name": "Gift", "type": "income", "icon": "fa-gift", "color": "#f43f5e"},
    {"name": "Other Income", "type": "income", "icon": "fa-plus-circle", "color": "#84cc16"},
]
