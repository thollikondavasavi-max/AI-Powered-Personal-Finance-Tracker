"""Routes package for FinWise API."""
from .auth import auth_bp
from .dashboard import dashboard_bp
from .transactions import transactions_bp
from .categories import categories_bp
from .budget import budget_bp
from .ai import ai_bp
from .pages import pages_bp
from .charts import charts_bp
from .profile import profile_bp

__all__ = [
    "auth_bp", "dashboard_bp", "transactions_bp",
    "categories_bp", "budget_bp", "ai_bp", "pages_bp",
    "charts_bp", "profile_bp"
]
