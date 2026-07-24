"""
AI / Machine Learning routes for FinWise.
Provides expense category prediction, spending forecasts, and financial insights.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import extract
from models.base import db
from models.transaction import Transaction
from models.user import User
from services.finance_service import FinanceService

ai_bp = Blueprint("ai", __name__)


def get_predictor():
    """Lazy-load the ML predictors (avoids startup delay)."""
    if not hasattr(current_app, "_category_predictor"):
        from ml.category_predictor import CategoryPredictor
        current_app._category_predictor = CategoryPredictor()
    return current_app._category_predictor


def get_expense_predictor():
    """Lazy-load the expense predictor."""
    if not hasattr(current_app, "_expense_predictor"):
        from ml.expense_predictor import ExpensePredictor
        current_app._expense_predictor = ExpensePredictor()
    return current_app._expense_predictor


@ai_bp.route("/predict-category", methods=["POST"])
@jwt_required()
def predict_category():
    """
    Predict expense category from transaction description.
    Uses Logistic Regression / Naive Bayes NLP classifier.

    Body: { "description": "swiggy order food" }
    Returns: predicted category + confidence score + top 3 alternatives
    """
    data = request.get_json()
    if not data or not data.get("description"):
        return jsonify({"error": "Description is required."}), 400

    description = data["description"].strip()
    if len(description) < 2:
        return jsonify({"error": "Description too short."}), 400

    predictor = get_predictor()

    # Get single best prediction
    predicted_category, confidence = predictor.predict(description)

    # Get top 3 alternatives
    top3 = predictor.predict_top3(description)

    return jsonify({
        "description": description,
        "predicted_category": predicted_category,
        "confidence": confidence,
        "alternatives": top3,
        "model": "TF-IDF + Logistic Regression",
    }), 200


@ai_bp.route("/predict-expense", methods=["POST"])
@jwt_required()
def predict_expense():
    """
    Predict next month's total expenses using ML.
    Uses Linear Regression and Random Forest Regressor ensemble.

    Returns: predicted amount, trend, confidence level
    """
    user_id = int(get_jwt_identity())

    # Get last 12 months of data for the model
    monthly_data = _get_monthly_data(user_id, months=12)

    predictor = get_expense_predictor()
    prediction = predictor.predict_next_month(monthly_data)

    # Add month context
    next_month = (datetime.now().month % 12) + 1
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    prediction["next_month_name"] = month_names[next_month - 1]
    prediction["current_month_expense"] = monthly_data[-1]["expense"] if monthly_data else 0

    return jsonify({"prediction": prediction}), 200


@ai_bp.route("/budget-recommendation", methods=["GET"])
@jwt_required()
def budget_recommendation():
    """
    Recommend an ideal monthly budget based on historical spending.
    Follows the 50/30/20 rule.
    """
    user_id = int(get_jwt_identity())

    # Get recent income for reference
    monthly_data = _get_monthly_data(user_id, months=6)

    # Calculate average monthly income
    avg_income = None
    if monthly_data:
        incomes = [d["income"] for d in monthly_data if d["income"] > 0]
        avg_income = sum(incomes) / len(incomes) if incomes else None

    predictor = get_expense_predictor()
    recommendation = predictor.recommend_budget(monthly_data, avg_income)

    return jsonify({"recommendation": recommendation}), 200


@ai_bp.route("/insights", methods=["GET"])
@jwt_required()
def get_insights():
    """
    Generate smart financial insights based on the user's spending patterns.
    Returns a list of personalized insight messages.
    """
    user_id = int(get_jwt_identity())
    insights = FinanceService.get_smart_insights(user_id)
    return jsonify({"insights": insights}), 200


def _get_monthly_data(user_id, months=12):
    """
    Helper: get monthly income/expense totals for last N months.
    Used by the ML prediction models.
    """
    now = datetime.now()
    data = []

    for i in range(months - 1, -1, -1):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1

        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        ).all()

        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")

        data.append({
            "month": month,
            "year": year,
            "income": income,
            "expense": expense,
        })

    return data
