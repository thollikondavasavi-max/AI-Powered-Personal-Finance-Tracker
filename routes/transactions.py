"""
Transaction routes for FinWise.
Full CRUD operations for income and expense transactions.
"""
import csv
import io
from datetime import datetime, date
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, extract
from models.base import db
from models.transaction import Transaction
from models.category import Category
from utils.validators import validate_transaction

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("", methods=["GET"])
@jwt_required()
def get_transactions():
    """
    Get user transactions with pagination, search, filter, and sort.
    Query params:
      - page: page number (default 1)
      - per_page: items per page (default 10, max 50)
      - search: search by description
      - type: filter by 'income' or 'expense'
      - category_id: filter by category
      - month: filter by month (1-12)
      - year: filter by year
      - sort: 'date_desc', 'date_asc', 'amount_desc', 'amount_asc'
    """
    user_id = int(get_jwt_identity())

    # --- Pagination params ---
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(50, max(1, request.args.get("per_page", 10, type=int)))

    # --- Base query ---
    query = Transaction.query.filter_by(user_id=user_id)

    # --- Filters ---
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    tx_type = request.args.get("type", "").strip().lower()
    if tx_type in ("income", "expense"):
        query = query.filter_by(type=tx_type)

    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)

    month = request.args.get("month", type=int)
    if month and 1 <= month <= 12:
        query = query.filter(extract("month", Transaction.date) == month)

    year = request.args.get("year", type=int)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)

    # --- Sorting ---
    sort = request.args.get("sort", "date_desc")
    sort_options = {
        "date_desc": Transaction.date.desc(),
        "date_asc": Transaction.date.asc(),
        "amount_desc": Transaction.amount.desc(),
        "amount_asc": Transaction.amount.asc(),
    }
    query = query.order_by(sort_options.get(sort, Transaction.date.desc()))

    # --- Paginate ---
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "transactions": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }), 200


@transactions_bp.route("", methods=["POST"])
@jwt_required()
def create_transaction():
    """Create a new transaction (income or expense)."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate input
    is_valid, error = validate_transaction(data)
    if not is_valid:
        return jsonify({"error": error}), 422

    # Parse date
    date_str = data.get("date", date.today().isoformat())
    try:
        tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        tx_date = date.today()

    # Validate category belongs to this user
    category_id = data.get("category_id")
    if category_id:
        cat = Category.query.filter(
            Category.id == category_id,
            or_(Category.user_id == user_id, Category.user_id == None)
        ).first()
        if not cat:
            return jsonify({"error": "Invalid category."}), 400

    transaction = Transaction(
        user_id=user_id,
        category_id=category_id,
        type=data["type"].lower(),
        amount=float(data["amount"]),
        description=data["description"].strip(),
        notes=data.get("notes", "").strip() or None,
        date=tx_date,
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "message": "Transaction added successfully.",
        "transaction": transaction.to_dict(),
    }), 201


@transactions_bp.route("/<int:tx_id>", methods=["PUT"])
@jwt_required()
def update_transaction(tx_id):
    """Update an existing transaction."""
    user_id = int(get_jwt_identity())

    transaction = Transaction.query.filter_by(id=tx_id, user_id=user_id).first()
    if not transaction:
        return jsonify({"error": "Transaction not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate
    is_valid, error = validate_transaction(data)
    if not is_valid:
        return jsonify({"error": error}), 422

    # Update fields
    transaction.type = data["type"].lower()
    transaction.amount = float(data["amount"])
    transaction.description = data["description"].strip()
    transaction.notes = data.get("notes", "").strip() or None

    date_str = data.get("date")
    if date_str:
        try:
            transaction.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    category_id = data.get("category_id")
    if category_id:
        transaction.category_id = category_id

    db.session.commit()

    return jsonify({
        "message": "Transaction updated successfully.",
        "transaction": transaction.to_dict(),
    }), 200


@transactions_bp.route("/<int:tx_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(tx_id):
    """Delete a transaction."""
    user_id = int(get_jwt_identity())

    transaction = Transaction.query.filter_by(id=tx_id, user_id=user_id).first()
    if not transaction:
        return jsonify({"error": "Transaction not found."}), 404

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({"message": "Transaction deleted successfully."}), 200


@transactions_bp.route("/export", methods=["GET"])
@jwt_required()
def export_csv():
    """Export transactions as CSV file."""
    user_id = int(get_jwt_identity())

    # Same filters as GET /transactions
    query = Transaction.query.filter_by(user_id=user_id)

    tx_type = request.args.get("type", "").strip().lower()
    if tx_type in ("income", "expense"):
        query = query.filter_by(type=tx_type)

    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    if month:
        query = query.filter(extract("month", Transaction.date) == month)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)

    transactions = query.order_by(Transaction.date.desc()).all()

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(["Date", "Type", "Category", "Description", "Amount (INR)", "Notes"])

    for t in transactions:
        writer.writerow([
            t.date.isoformat() if t.date else "",
            t.type.capitalize(),
            t.category.name if t.category else "Uncategorized",
            t.description,
            f"{t.amount:.2f}",
            t.notes or "",
        ])

    output.seek(0)
    csv_data = output.getvalue()

    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=finwise_transactions.csv"
    return response
