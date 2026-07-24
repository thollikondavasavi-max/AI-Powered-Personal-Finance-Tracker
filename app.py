"""
FinWise – AI Powered Smart Personal Finance Tracker
Main Flask application entry point.

Run with: python app.py
"""
import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import AppConfig
from models.base import db


def create_app():
    """Application factory: create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(AppConfig)

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins="*", supports_credentials=True)

    jwt = JWTManager(app)

    # JWT error handlers
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authentication required. Please log in."}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token. Please log in again."}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Session expired. Please log in again."}), 401

    # Register blueprints (group related routes together)
    from routes.pages import pages_bp
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.transactions import transactions_bp
    from routes.categories import categories_bp
    from routes.budget import budget_bp
    from routes.ai import ai_bp
    from routes.charts import charts_bp
    from routes.profile import profile_bp

    # Page routes (serve HTML)
    app.register_blueprint(pages_bp)

    # API routes (return JSON)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(budget_bp, url_prefix="/api/budget")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(charts_bp, url_prefix="/api/charts")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")

    # Health check endpoint
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "app": "FinWise"}), 200

    # Inject google_client_id into every template context so login/signup
    # pages can conditionally render the Google Sign-In button.
    @app.context_processor
    def inject_google():
        return {"google_client_id": app.config.get("GOOGLE_CLIENT_ID", "")}

    # Create database tables on first run
    with app.app_context():
        db.create_all()
        _seed_demo_data(app)

    return app


def _seed_demo_data(app):
    """Seed demo data so the app looks alive on first launch."""
    from models.user import User
    from models.category import Category, DEFAULT_CATEGORIES
    from models.transaction import Transaction
    from models.budget import Budget
    from datetime import date, timedelta
    import bcrypt
    import random

    # Only seed if no users exist yet
    if User.query.count() > 0:
        return

    # Create a demo user
    salt = bcrypt.gensalt(rounds=12)
    pwd_hash = bcrypt.hashpw(b"demo1234", salt).decode("utf-8")

    demo_user = User(
        username="demo",
        email="demo@finwise.app",
        password_hash=pwd_hash,
        full_name="Alex Johnson",
        currency="INR",
    )
    db.session.add(demo_user)
    db.session.flush()

    # Add default categories for demo user
    categories = {}
    for cat_data in DEFAULT_CATEGORIES:
        cat = Category(
            user_id=demo_user.id,
            name=cat_data["name"],
            type=cat_data["type"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            is_default=True,
        )
        db.session.add(cat)
        db.session.flush()
        categories[cat_data["name"]] = cat

    # Seed 3 months of transactions
    today = date.today()
    expense_cats = ["Food & Dining", "Shopping", "Travel", "Bills & Utilities", "Entertainment", "Fuel", "Medical"]
    income_cats = ["Salary", "Freelance"]

    income_descriptions = {
        "Salary": ["Monthly salary", "Salary credit", "Payroll"],
        "Freelance": ["Freelance project", "Client payment", "Web design work"],
    }
    expense_data = {
        "Food & Dining": [("Swiggy order", 350), ("Zomato delivery", 280), ("Restaurant dinner", 850), ("Grocery shopping", 1200), ("Coffee shop", 180)],
        "Shopping": [("Amazon purchase", 1500), ("Clothing store", 2200), ("Electronics", 3500)],
        "Travel": [("Uber ride", 220), ("Metro card recharge", 500), ("Flight tickets", 8500)],
        "Bills & Utilities": [("Electricity bill", 1200), ("Internet bill", 799), ("Mobile recharge", 399), ("Netflix subscription", 649)],
        "Entertainment": [("Movie tickets", 600), ("Gaming", 299), ("Spotify premium", 119)],
        "Fuel": [("Petrol fill", 1500), ("Fuel top-up", 800)],
        "Medical": [("Pharmacy", 450), ("Doctor consultation", 800)],
    }

    for months_back in range(3, -1, -1):
        # Calculate the month
        month_date = today.replace(day=1) - timedelta(days=months_back * 30)

        # Add salary income (1st of each month)
        salary_cat = categories.get("Salary")
        if salary_cat:
            tx = Transaction(
                user_id=demo_user.id,
                category_id=salary_cat.id,
                type="income",
                amount=75000.0,
                description="Monthly salary credit",
                date=month_date,
            )
            db.session.add(tx)

        # Add freelance income mid-month
        freelance_cat = categories.get("Freelance")
        if freelance_cat and random.random() > 0.4:
            tx = Transaction(
                user_id=demo_user.id,
                category_id=freelance_cat.id,
                type="income",
                amount=random.choice([15000, 20000, 12000]),
                description="Freelance project payment",
                date=month_date + timedelta(days=15),
            )
            db.session.add(tx)

        # Add various expenses throughout the month
        for cat_name, txn_list in expense_data.items():
            cat = categories.get(cat_name)
            if not cat:
                continue
            # Add 2-4 transactions per category per month
            for _ in range(random.randint(1, 3)):
                desc, base_amount = random.choice(txn_list)
                amount = base_amount * (0.85 + random.random() * 0.3)
                day_offset = random.randint(1, 27)
                tx = Transaction(
                    user_id=demo_user.id,
                    category_id=cat.id,
                    type="expense",
                    amount=round(amount, 2),
                    description=desc,
                    date=month_date + timedelta(days=day_offset),
                )
                db.session.add(tx)

    # Set a demo budget
    budget = Budget(
        user_id=demo_user.id,
        month=today.month,
        year=today.year,
        total_budget=50000.0,
        alert_threshold=80.0,
    )
    db.session.add(budget)

    # Add sample savings goals
    from models.budget import SavingsGoal
    goals_data = [
        {"name": "Emergency Fund", "target_amount": 300000, "current_amount": 85000, "icon": "fa-piggy-bank", "color": "#6366f1"},
        {"name": "New Laptop", "target_amount": 80000, "current_amount": 35000, "icon": "fa-laptop", "color": "#a855f7"},
        {"name": "Goa Trip", "target_amount": 50000, "current_amount": 18000, "icon": "fa-plane", "color": "#06b6d4"},
    ]
    from datetime import date as _date
    for g in goals_data:
        goal = SavingsGoal(
            user_id=demo_user.id,
            name=g["name"],
            target_amount=g["target_amount"],
            current_amount=g["current_amount"],
            icon=g["icon"],
            color=g["color"],
        )
        db.session.add(goal)

    db.session.commit()
    print("✅ Demo data seeded successfully. Login with: demo / demo1234")


# Run the application
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
