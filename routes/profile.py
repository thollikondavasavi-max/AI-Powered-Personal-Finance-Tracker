"""
Profile routes for FinWise.
User profile management including avatar upload.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.base import db
from models.user import User

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("", methods=["GET"])
@jwt_required()
def get_profile():
    """Get full user profile."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
