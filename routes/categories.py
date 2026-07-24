"""
Category routes for FinWise.
Manage expense and income categories (default + custom).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from models.base import db
from models.category import Category
from models.transaction import Transaction

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("", methods=["GET"])
@jwt_required()
def get_categories():
    """Get all categories available to the user (default + custom)."""
    user_id = int(get_jwt_identity())

    cat_type = request.args.get("type", "").strip().lower()

    # Include user's categories + globally shared defaults (user_id=None)
    query = Category.query.filter(
        or_(Category.user_id == user_id, Category.user_id == None)
    )

    if cat_type in ("income", "expense"):
        query = query.filter_by(type=cat_type)

    categories = query.order_by(Category.is_default.desc(), Category.name).all()

    return jsonify({"categories": [c.to_dict() for c in categories]}), 200


@categories_bp.route("", methods=["POST"])
@jwt_required()
def create_category():
    """Create a custom category for the user."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "").strip()
    cat_type = data.get("type", "").strip().lower()

    if not name:
        return jsonify({"error": "Category name is required."}), 422
    if len(name) > 50:
        return jsonify({"error": "Category name must be at most 50 characters."}), 422
    if cat_type not in ("income", "expense"):
        return jsonify({"error": "Category type must be 'income' or 'expense'."}), 422

    # Check for duplicate category name for this user
    existing = Category.query.filter(
        or_(Category.user_id == user_id, Category.user_id == None),
        Category.name == name,
        Category.type == cat_type,
    ).first()
    if existing:
        return jsonify({"error": f"Category '{name}' already exists."}), 409

    category = Category(
        user_id=user_id,
        name=name,
        type=cat_type,
        icon=data.get("icon", "fa-tag"),
        color=data.get("color", "#6366f1"),
        is_default=False,
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({
        "message": "Category created successfully.",
        "category": category.to_dict(),
    }), 201


@categories_bp.route("/<int:cat_id>", methods=["PUT"])
@jwt_required()
def update_category(cat_id):
    """Update a user-created category."""
    user_id = int(get_jwt_identity())

    # Only allow editing user's own categories (not system defaults)
    category = Category.query.filter_by(id=cat_id, user_id=user_id).first()
    if not category:
        return jsonify({"error": "Category not found or you don't have permission to edit it."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "name" in data:
        category.name = data["name"].strip()[:50]
    if "icon" in data:
        category.icon = data["icon"]
    if "color" in data:
        category.color = data["color"]

    db.session.commit()
    return jsonify({"message": "Category updated.", "category": category.to_dict()}), 200


@categories_bp.route("/<int:cat_id>", methods=["DELETE"])
@jwt_required()
def delete_category(cat_id):
    """Delete a user-created category."""
    user_id = int(get_jwt_identity())

    category = Category.query.filter_by(id=cat_id, user_id=user_id).first()
    if not category:
        return jsonify({"error": "Category not found or you don't have permission to delete it."}), 404

    if category.is_default:
        return jsonify({"error": "Cannot delete a default category."}), 403

    # Unlink transactions from this category before deleting
    Transaction.query.filter_by(category_id=cat_id, user_id=user_id).update(
        {"category_id": None}
    )

    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category deleted."}), 200
