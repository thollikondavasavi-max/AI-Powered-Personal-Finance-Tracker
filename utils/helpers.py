"""
Helper utilities for FinWise.
Common helper functions used across the application.
"""
import os
from datetime import datetime


def format_currency(amount, currency="INR"):
    """Format a number as currency string."""
    if currency == "INR":
        return f"₹{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f}"


def format_date(date_obj):
    """Format a date object to human-readable string."""
    if not date_obj:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%d %b %Y")


def paginate_query(query, page=1, per_page=10):
    """
    Paginate a SQLAlchemy query.
    Returns paginated results and metadata.
    """
    page = max(1, int(page))
    per_page = min(100, max(1, int(per_page)))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": pagination.items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


def allowed_file(filename, allowed_extensions):
    """Check if a filename has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def get_month_name(month_number):
    """Convert month number (1-12) to month name."""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    if 1 <= month_number <= 12:
        return months[month_number - 1]
    return "Unknown"


def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    return round(((new_value - old_value) / abs(old_value)) * 100, 2)


def sanitize_filename(filename):
    """Remove unsafe characters from a filename."""
    import re
    filename = re.sub(r"[^\w\s\-\.]", "", filename)
    filename = re.sub(r"\s+", "_", filename)
    return filename[:200]
