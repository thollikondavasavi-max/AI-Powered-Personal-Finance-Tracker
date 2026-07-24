"""
Budget routes for FinWise.
Manage monthly budgets, budget alerts, and savings goals.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.base import db
from models.budget import Budget, BudgetCategory, SavingsGoal
from models.category import Category
from services.finance_service import FinanceService
from utils.validators import validate_budget

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("", methods=["GET"])
@jwt_required()
def get_budget():
    """Get budget for a given month/year with spending status."""
    user_id = int(get_jwt_identity())
    now = datetime.now()
    month = request.args.get("month", now.month, type=int)
    year = request.args.get("year", now.year, type=int)

    budget_status = FinanceService.get_budget_status(user_id, month, year)

    if not budget_status:
        return jsonify({"budget": None, "message": "No budget set for this month."}), 200

    return jsonify(budget_status), 200


@budget_bp.route("", methods=["POST"])
@jwt_required()
def create_or_update_budget():
    """Create or update the monthly budget."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    now = datetime.now()
    month = data.get("month", now.month)
    year = data.get("year", now.year)

    # Validate input
    is_valid, error = validate_budget(data)
    if not is_valid:
        return jsonify({"error": error}), 422

    # Check if budget already exists for this month
    budget = Budget.query.filter_by(user_id=user_id, month=month, year=year).first()

    if budget:
        # Update existing budget
        budget.total_budget = float(data["total_budget"])
        budget.alert_threshold = float(data.get("alert_threshold", 80.0))
    else:
        # Create new budget
        budget = Budget(
            user_id=user_id,
            month=month,
            year=year,
            total_budget=float(data["total_budget"]),
            alert_threshold=float(data.get("alert_threshold", 80.0)),
        )
        db.session.add(budget)
        db.session.flush()

    # Handle category-level budgets if provided
    if "category_budgets" in data and isinstance(data["category_budgets"], list):
        # Remove old category budgets for this budget
        BudgetCategory.query.filter_by(budget_id=budget.id).delete()

        for cb_data in data["category_budgets"]:
            cat_id = cb_data.get("category_id")
            amount = cb_data.get("allocated_amount", 0)
            if cat_id and float(amount) > 0:
                cb = BudgetCategory(
                    budget_id=budget.id,
                    category_id=cat_id,
                    allocated_amount=float(amount),
                )
                db.session.add(cb)

    db.session.commit()

    # Return updated status
    budget_status = FinanceService.get_budget_status(user_id, month, year)
    return jsonify({
        "message": "Budget saved successfully.",
        "budget": budget_status,
    }), 200


@budget_bp.route("/<int:budget_id>", methods=["DELETE"])
@jwt_required()
def delete_budget(budget_id):
    """Delete a budget."""
    user_id = int(get_jwt_identity())

    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
    if not budget:
        return jsonify({"error": "Budget not found."}), 404

    db.session.delete(budget)
    db.session.commit()

    return jsonify({"message": "Budget deleted."}), 200


# --- Savings Goals ---

@budget_bp.route("/savings-goals", methods=["GET"])
@jwt_required()
def get_savings_goals():
    """Get all savings goals for the user."""
    user_id = int(get_jwt_identity())
    goals = SavingsGoal.query.filter_by(user_id=user_id).order_by(SavingsGoal.created_at.desc()).all()
    return jsonify({"goals": [g.to_dict() for g in goals]}), 200


@budget_bp.route("/savings-goals", methods=["POST"])
@jwt_required()
def create_savings_goal():
    """Create a new savings goal."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Goal name is required."}), 422

    try:
        target = float(data.get("target_amount", 0))
        if target <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Target amount must be a positive number."}), 422

    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        except ValueError:
            pass

    goal = SavingsGoal(
        user_id=user_id,
        name=name,
        target_amount=target,
        current_amount=float(data.get("current_amount", 0)),
        deadline=deadline,
        icon=data.get("icon", "fa-bullseye"),
        color=data.get("color", "#6366f1"),
    )
    db.session.add(goal)
    db.session.commit()

    return jsonify({"message": "Savings goal created.", "goal": goal.to_dict()}), 201


@budget_bp.route("/savings-goals/<int:goal_id>", methods=["PUT"])
@jwt_required()
def update_savings_goal(goal_id):
    """Update a savings goal (e.g., add progress)."""
    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"error": "Goal not found."}), 404

    data = request.get_json()
    if "name" in data:
        goal.name = data["name"].strip()
    if "target_amount" in data:
        goal.target_amount = float(data["target_amount"])
    if "current_amount" in data:
        goal.current_amount = float(data["current_amount"])
        goal.is_completed = goal.current_amount >= goal.target_amount
    if "deadline" in data and data["deadline"]:
        try:
            goal.deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        except ValueError:
            pass

    db.session.commit()
    return jsonify({"message": "Goal updated.", "goal": goal.to_dict()}), 200


@budget_bp.route("/savings-goals/<int:goal_id>", methods=["DELETE"])
@jwt_required()
def delete_savings_goal(goal_id):
    """Delete a savings goal."""
    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"error": "Goal not found."}), 404

    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": "Goal deleted."}), 200
