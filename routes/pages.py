"""
Page routes for FinWise.
Serves HTML templates for each page of the application.
"""
from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    """Landing / home page."""
    return render_template("index.html")


@pages_bp.route("/login")
def login_page():
    """Login page."""
    return render_template("auth/login.html")


@pages_bp.route("/signup")
def signup_page():
    """Signup / registration page."""
    return render_template("auth/signup.html")


@pages_bp.route("/dashboard")
def dashboard_page():
    """Main dashboard page (requires auth via JS)."""
    return render_template("dashboard/index.html")


@pages_bp.route("/transactions")
def transactions_page():
    """Transactions management page."""
    return render_template("transactions/index.html")


@pages_bp.route("/budget")
def budget_page():
    """Budget management and savings goals page."""
    return render_template("budget/index.html")


@pages_bp.route("/charts")
def charts_page():
    """Charts and analytics page."""
    return render_template("charts/index.html")


@pages_bp.route("/insights")
def insights_page():
    """AI insights and predictions page."""
    return render_template("ai/insights.html")


@pages_bp.route("/profile")
def profile_page():
    """User profile page."""
    return render_template("profile/index.html")
