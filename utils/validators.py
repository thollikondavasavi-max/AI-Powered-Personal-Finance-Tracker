"""
Input validators for FinWise.
Validates user input before processing to prevent invalid data and security issues.
"""
import re
from datetime import datetime


def validate_user_registration(data):
    """
    Validate user registration input.
    Returns (is_valid, error_message) tuple.
    """
    errors = []

    # Username: 3-50 chars, alphanumeric + underscore
    username = data.get("username", "").strip()
    if not username:
        errors.append("Username is required.")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters.")
    elif len(username) > 50:
        errors.append("Username must be at most 50 characters.")
    elif not re.match(r"^[a-zA-Z0-9_]+$", username):
        errors.append("Username can only contain letters, numbers, and underscores.")

    # Email: must be valid format
    email = data.get("email", "").strip().lower()
    if not email:
        errors.append("Email is required.")
    elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors.append("Please enter a valid email address.")

    # Password: min 8 chars
    password = data.get("password", "")
    if not password:
        errors.append("Password is required.")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters.")

    # Full name (optional but validate if provided)
    full_name = data.get("full_name", "").strip()
    if full_name and len(full_name) > 100:
        errors.append("Full name must be at most 100 characters.")

    if errors:
        return False, " ".join(errors)
    return True, None


def validate_transaction(data):
    """
    Validate transaction input.
    Returns (is_valid, error_message) tuple.
    """
    errors = []

    # Type must be 'income' or 'expense'
    tx_type = data.get("type", "").strip().lower()
    if tx_type not in ("income", "expense"):
        errors.append("Transaction type must be 'income' or 'expense'.")

    # Amount must be a positive number
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            errors.append("Amount must be greater than 0.")
        if amount > 999999999:
            errors.append("Amount is too large.")
    except (TypeError, ValueError):
        errors.append("Amount must be a valid number.")

    # Description is required
    description = data.get("description", "").strip()
    if not description:
        errors.append("Description is required.")
    elif len(description) > 200:
        errors.append("Description must be at most 200 characters.")

    # Date validation
    date_str = data.get("date")
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append("Date must be in YYYY-MM-DD format.")

    if errors:
        return False, " ".join(errors)
    return True, None


def validate_budget(data):
    """
    Validate budget input.
    Returns (is_valid, error_message) tuple.
    """
    errors = []

    # Total budget must be positive
    try:
        total = float(data.get("total_budget", 0))
        if total <= 0:
            errors.append("Total budget must be greater than 0.")
    except (TypeError, ValueError):
        errors.append("Total budget must be a valid number.")

    # Month must be 1-12
    month = data.get("month")
    if month is not None:
        try:
            month = int(month)
            if not 1 <= month <= 12:
                errors.append("Month must be between 1 and 12.")
        except (TypeError, ValueError):
            errors.append("Month must be a valid number.")

    # Year must be reasonable
    year = data.get("year")
    if year is not None:
        try:
            year = int(year)
            if not 2000 <= year <= 2100:
                errors.append("Year must be between 2000 and 2100.")
        except (TypeError, ValueError):
            errors.append("Year must be a valid number.")

    if errors:
        return False, " ".join(errors)
    return True, None
