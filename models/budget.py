"""
Budget models for FinWise.
Manages monthly budgets, category-level budgets, and savings goals.
"""
from datetime import datetime
from .base import db


class Budget(db.Model):
    """Monthly budget model."""

    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Owner
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Budget period
    month = db.Column(db.Integer, nullable=False)   # 1-12
    year = db.Column(db.Integer, nullable=False)

    # Budget amounts
    total_budget = db.Column(db.Float, nullable=False, default=0.0)

    # Alert threshold (e.g., 80 means alert when 80% is spent)
    alert_threshold = db.Column(db.Float, default=80.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Category-level budget breakdown
    category_budgets = db.relationship(
        "BudgetCategory", backref="budget", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "month": self.month,
            "year": self.year,
            "total_budget": self.total_budget,
            "alert_threshold": self.alert_threshold,
            "category_budgets": [cb.to_dict() for cb in self.category_budgets],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BudgetCategory(db.Model):
    """Per-category budget allocation within a monthly budget."""

    __tablename__ = "budget_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    budget_id = db.Column(db.Integer, db.ForeignKey("budgets.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    allocated_amount = db.Column(db.Float, nullable=False, default=0.0)

    # Reference to the category object
    category = db.relationship("Category", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "budget_id": self.budget_id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "allocated_amount": self.allocated_amount,
        }


class SavingsGoal(db.Model):
    """Savings goal tracker."""

    __tablename__ = "savings_goals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.Date, nullable=True)
    icon = db.Column(db.String(50), default="fa-bullseye")
    color = db.Column(db.String(20), default="#6366f1")

    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        progress = (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "icon": self.icon,
            "color": self.color,
            "is_completed": self.is_completed,
            "progress_percent": round(min(progress, 100), 1),
        }
