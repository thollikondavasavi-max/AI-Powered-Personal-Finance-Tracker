"""
Authentication routes for FinWise.
Handles user registration, login, logout, and profile management.
"""
import os
import bcrypt
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, create_refresh_token
)
from models.base import db
from models.user import User
from models.category import Category, DEFAULT_CATEGORIES
from utils.validators import validate_user_registration
from werkzeug.utils import secure_filename

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/google", methods=["POST"])
def google_login():
    """Verify a Google Identity Services credential (ID token) and log the user in."""
    import urllib.request
    import urllib.error
    import json as json_lib

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    credential = data.get("credential", "").strip()
    if not credential:
        return jsonify({"error": "No Google credential provided"}), 400

    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return jsonify({
            "error": "Google Sign-In is not configured on this server. "
                     "Add GOOGLE_CLIENT_ID to your environment secrets."
        }), 503

    # Verify the ID token with Google's public tokeninfo endpoint
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            google_data = json_lib.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        current_app.logger.error(f"Google tokeninfo error: {body}")
        return jsonify({"error": "Google token verification failed. Please try again."}), 401
    except Exception as e:
        current_app.logger.error(f"Google token request error: {e}")
        return jsonify({"error": "Could not reach Google to verify token."}), 503

    # Validate audience
    token_aud = google_data.get("aud", "")
    if token_aud != client_id:
        return jsonify({"error": "Token audience mismatch — please use the correct app."}), 401

    email = (google_data.get("email") or "").lower().strip()
    name = google_data.get("name", "")
    picture = google_data.get("picture", "")

    if not email:
        return jsonify({"error": "No email found in your Google account."}), 400

    if not google_data.get("email_verified"):
        return jsonify({"error": "Your Google email is not verified."}), 400

    # Find existing user or create a new one
    user = User.query.filter_by(email=email).first()

    if not user:
        # Build a unique username from the email prefix
        base = email.split("@")[0].lower().replace(".", "_").replace("+", "_")[:20]
        username = base
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base}{counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            password_hash="__google_oauth__",   # sentinel — not a real hash
            full_name=name or username,
            profile_pic=picture or None,
            currency="INR",
        )
        db.session.add(user)
        db.session.flush()

        # Seed default categories for the new user
        from models.category import Category, DEFAULT_CATEGORIES
        for cat_data in DEFAULT_CATEGORIES:
            cat = Category(
                user_id=user.id,
                name=cat_data["name"],
                type=cat_data["type"],
                icon=cat_data["icon"],
                color=cat_data["color"],
                is_default=True,
            )
            db.session.add(cat)

        db.session.commit()
        is_new = True
    else:
        # Update profile picture if Google provides one and user has none
        if picture and not user.profile_pic:
            user.profile_pic = picture
            db.session.commit()
        is_new = False

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
        "message": f"Welcome{'to FinWise' if is_new else ' back'}, {user.full_name or user.username}!",
        "is_new_user": is_new,
    }), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate input
    is_valid, error_msg = validate_user_registration(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 422

    username = data["username"].strip().lower()
    email = data["email"].strip().lower()

    # Check if username or email already exists (prevents duplicate accounts)
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken. Please choose another."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered. Please login instead."}), 409

    # Hash the password using bcrypt (never store plain text passwords)
    password_bytes = data["password"].encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = good security/speed balance
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    # Create the new user
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=data.get("full_name", "").strip(),
    )
    db.session.add(user)
    db.session.flush()  # Flush to get the user.id before committing

    # Create default categories for this user
    for cat_data in DEFAULT_CATEGORIES:
        category = Category(
            user_id=user.id,
            name=cat_data["name"],
            type=cat_data["type"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            is_default=True,
        )
        db.session.add(category)

    db.session.commit()

    # Generate JWT tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Account created successfully! Welcome to FinWise.",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    identifier = data.get("identifier", "").strip().lower()  # username or email
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"error": "Username/email and password are required."}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user:
        return jsonify({"error": "Invalid credentials. Please check and try again."}), 401

    # Verify password using bcrypt
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"error": "Invalid credentials. Please check and try again."}), 401

    if not user.is_active:
        return jsonify({"error": "Your account has been deactivated."}), 403

    # Issue JWT tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": f"Welcome back, {user.full_name or user.username}!",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Issue a new access token using a valid refresh token."""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Get the currently logged-in user's profile."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update user profile information."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update allowed fields
    if "full_name" in data:
        user.full_name = data["full_name"].strip()[:100]
    if "phone" in data:
        user.phone = data["phone"].strip()[:20]
    if "currency" in data and data["currency"] in ("INR", "USD", "EUR", "GBP"):
        user.currency = data["currency"]

    db.session.commit()
    return jsonify({"message": "Profile updated successfully.", "user": user.to_dict()}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """Change user password."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not bcrypt.checkpw(current_password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"error": "Current password is incorrect."}), 401

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters."}), 422

    salt = bcrypt.gensalt(rounds=12)
    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode("utf-8")
    db.session.commit()

    return jsonify({"message": "Password changed successfully."}), 200


@auth_bp.route("/upload-avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """Upload a profile picture."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected."}), 400

    allowed = {"png", "jpg", "jpeg", "gif", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        return jsonify({"error": "Invalid file type. Use PNG, JPG, GIF, or WebP."}), 400

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"avatar_{user_id}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    user.profile_pic = f"/static/uploads/{filename}"
    db.session.commit()

    return jsonify({
        "message": "Profile picture updated.",
        "profile_pic": user.profile_pic,
    }), 200
