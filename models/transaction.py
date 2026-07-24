"""
Transaction model for FinWise.
Records every income and expense transaction for a user.
"""
from datetime import datetime
from .base import db


class Transaction(db.Model):
    """Financial transaction model."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Owner
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Category reference
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    # Transaction details
    type = db.Column(db.String(10), nullable=False)        # 'income' or 'expense'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert transaction to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "Uncategorized",
            "category_icon": self.category.icon if self.category else "fa-tag",
            "category_color": self.category.color if self.category else "#94a3b8",
            "type": self.type,
            "amount": self.amount,
            "description": self.description,
            "notes": self.notes,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Transaction {self.type} {self.amount}>"
