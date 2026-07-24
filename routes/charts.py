"""
Chart data routes for FinWise.
Provides formatted data for all Chart.js visualizations.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import extract, func
from models.base import db
from models.transaction import Transaction
from models.category import Category
from services.finance_service import FinanceService

charts_bp = Blueprint("charts", __name__)


@charts_bp.route("/income-vs-expense", methods=["GET"])
@jwt_required()
def income_vs_expense():
    """Bar chart: monthly income vs expense for last 6 months."""
    user_id = int(get_jwt_identity())
    months = request.args.get("months", 6, type=int)
    trend = FinanceService.get_monthly_trend(user_id, months)

    return jsonify({
        "labels": [f"{d['month']} {d['year']}" for d in trend],
        "income": [d["income"] for d in trend],
        "expense": [d["expense"] for d in trend],
        "savings": [d["savings"] for d in trend],
    }), 200


@charts_bp.route("/category-pie", methods=["GET"])
@jwt_required()
def category_pie():
    """Pie chart: expense breakdown by category."""
    user_id = int(get_jwt_identity())
    now = datetime.now()
    month = request.args.get("month", now.month, type=int)
    year = request.args.get("year", now.year, type=int)

    breakdown = FinanceService.get_category_breakdown(user_id, month, year)

    return jsonify({
        "labels": [d["name"] for d in breakdown],
        "data": [d["amount"] for d in breakdown],
        "colors": [d["color"] for d in breakdown],
        "percentages": [d["percentage"] for d in breakdown],
    }), 200


@charts_bp.route("/savings-trend", methods=["GET"])
@jwt_required()
def savings_trend():
    """Line chart: savings trend over time."""
    user_id = int(get_jwt_identity())
    months = request.args.get("months", 6, type=int)
    trend = FinanceService.get_monthly_trend(user_id, months)

    cumulative_savings = 0
    cumulative = []
    for d in trend:
        cumulative_savings += d["savings"]
        cumulative.append(round(cumulative_savings, 2))

    return jsonify({
        "labels": [f"{d['month']}" for d in trend],
        "monthly_savings": [d["savings"] for d in trend],
        "cumulative_savings": cumulative,
    }), 200


@charts_bp.route("/weekly-spending", methods=["GET"])
@jwt_required()
def weekly_spending():
    """Bar chart: daily spending for the current week."""
    user_id = int(get_jwt_identity())
    weekly = FinanceService.get_weekly_spending(user_id)

    return jsonify({
        "labels": [d["day"] for d in weekly],
        "amounts": [d["amount"] for d in weekly],
        "is_today": [d["is_today"] for d in weekly],
    }), 200


@charts_bp.route("/budget-progress", methods=["GET"])
@jwt_required()
def budget_progress():
    """Doughnut chart: budget usage progress."""
    user_id = int(get_jwt_identity())
    now = datetime.now()
    month = request.args.get("month", now.month, type=int)
    year = request.args.get("year", now.year, type=int)

    from models.budget import Budget
    from services.finance_service import FinanceService

    budget_status = FinanceService.get_budget_status(user_id, month, year)

    if not budget_status:
        return jsonify({"has_budget": False}), 200

    return jsonify({
        "has_budget": True,
        "total_budget": budget_status["budget"]["total_budget"],
        "total_spent": budget_status["total_spent"],
        "remaining": budget_status["remaining"],
        "percentage_used": budget_status["percentage_used"],
        "is_over_budget": budget_status["is_over_budget"],
    }), 200
