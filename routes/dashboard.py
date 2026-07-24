"""
Dashboard routes for FinWise.
Provides summary data for the main dashboard view.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.base import db
from models.transaction import Transaction
from models.user import User
from services.finance_service import FinanceService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_summary():
    """Get financial summary for the dashboard."""
    user_id = int(get_jwt_identity())

    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)

    summary = FinanceService.get_summary(user_id, month, year)
    budget_status = FinanceService.get_budget_status(user_id, month, year)

    return jsonify({
        "summary": summary,
        "budget": budget_status,
    }), 200


@dashboard_bp.route("/recent-transactions", methods=["GET"])
@jwt_required()
def get_recent_transactions():
    """Get recent transactions for the dashboard."""
    user_id = int(get_jwt_identity())
    limit = request.args.get("limit", 8, type=int)

    transactions = (
        Transaction.query.filter_by(user_id=user_id)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "transactions": [t.to_dict() for t in transactions]
    }), 200


@dashboard_bp.route("/monthly-trend", methods=["GET"])
@jwt_required()
def get_monthly_trend():
    """Get 6-month income vs expense trend."""
    user_id = int(get_jwt_identity())
    months = request.args.get("months", 6, type=int)
    trend = FinanceService.get_monthly_trend(user_id, months)
    return jsonify({"trend": trend}), 200


@dashboard_bp.route("/category-breakdown", methods=["GET"])
@jwt_required()
def get_category_breakdown():
    """Get expense breakdown by category."""
    user_id = int(get_jwt_identity())
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)

    breakdown = FinanceService.get_category_breakdown(user_id, month, year)
    return jsonify({"breakdown": breakdown}), 200


@dashboard_bp.route("/weekly-spending", methods=["GET"])
@jwt_required()
def get_weekly_spending():
    """Get spending for each day of the current week."""
    user_id = int(get_jwt_identity())
    weekly = FinanceService.get_weekly_spending(user_id)
    return jsonify({"weekly": weekly}), 200
