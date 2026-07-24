"""
Finance service for FinWise.
Contains business logic for financial calculations and data aggregation.
All DB lookups use SQL-level aggregation — no Python-side full-table loads.
"""
from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy import func, extract, case, and_
from models.base import db
from models.transaction import Transaction
from models.budget import Budget
from models.category import Category


class FinanceService:
    """Service class for financial data operations."""

    @staticmethod
    def get_summary(user_id, month=None, year=None):
        """
        Calculate financial summary using SQL aggregation (no full table scans).
        """
        now = datetime.now()
        month = month or now.month
        year = year or now.year

        # Monthly income + expense in ONE query
        monthly = db.session.query(
            func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)).label("income"),
            func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)).label("expense"),
        ).filter(
            Transaction.user_id == user_id,
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        ).one()

        # All-time balance in ONE query
        alltime = db.session.query(
            func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)).label("income"),
            func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)).label("expense"),
        ).filter(Transaction.user_id == user_id).one()

        monthly_income  = float(monthly.income  or 0)
        monthly_expense = float(monthly.expense or 0)
        monthly_savings = max(0, monthly_income - monthly_expense)
        all_income      = float(alltime.income  or 0)
        all_expense     = float(alltime.expense or 0)

        return {
            "month":            month,
            "year":             year,
            "monthly_income":   round(monthly_income, 2),
            "monthly_expense":  round(monthly_expense, 2),
            "monthly_savings":  round(monthly_savings, 2),
            "current_balance":  round(all_income - all_expense, 2),
            "total_income":     round(all_income, 2),
            "total_expense":    round(all_expense, 2),
        }

    @staticmethod
    def get_budget_status(user_id, month=None, year=None):
        """Get budget status using a single SQL aggregate for spending."""
        now = datetime.now()
        month = month or now.month
        year  = year  or now.year

        budget = Budget.query.filter_by(
            user_id=user_id, month=month, year=year
        ).first()

        if not budget:
            return None

        row = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0).label("total_spent")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            extract("month", Transaction.date) == month,
            extract("year",  Transaction.date) == year,
        ).one()

        total_spent    = float(row.total_spent)
        remaining      = budget.total_budget - total_spent
        percentage_used = (total_spent / budget.total_budget * 100) if budget.total_budget > 0 else 0

        return {
            "budget":           budget.to_dict(),
            "total_spent":      round(total_spent, 2),
            "remaining":        round(remaining, 2),
            "percentage_used":  round(percentage_used, 1),
            "is_over_budget":   total_spent > budget.total_budget,
            "is_near_limit":    percentage_used >= budget.alert_threshold,
        }

    @staticmethod
    def get_category_breakdown(user_id, month=None, year=None):
        """Get spending breakdown by category — single grouped query."""
        now   = datetime.now()
        month = month or now.month
        year  = year  or now.year

        results = db.session.query(
            Category.name,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        ).join(
            Transaction, Transaction.category_id == Category.id
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            extract("month", Transaction.date) == month,
            extract("year",  Transaction.date) == year,
        ).group_by(
            Category.id, Category.name, Category.icon, Category.color
        ).order_by(func.sum(Transaction.amount).desc()).all()

        total_expenses = sum(r.total for r in results)

        return [
            {
                "name":       r.name,
                "icon":       r.icon,
                "color":      r.color,
                "amount":     round(r.total, 2),
                "percentage": round((r.total / total_expenses * 100), 1) if total_expenses > 0 else 0,
            }
            for r in results
        ]

    @staticmethod
    def get_monthly_trend(user_id, months=6):
        """
        Get income vs expense for the last N months.
        Single query with GROUP BY instead of N separate queries.
        """
        now = datetime.now()

        # Build list of (year, month) tuples we want, oldest first
        periods = []
        for i in range(months - 1, -1, -1):
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            periods.append((y, m))

        # One query — group by year+month
        rows = db.session.query(
            extract("year",  Transaction.date).label("yr"),
            extract("month", Transaction.date).label("mo"),
            func.sum(case((Transaction.type == "income",  Transaction.amount), else_=0)).label("income"),
            func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)).label("expense"),
        ).filter(
            Transaction.user_id == user_id,
            # Only include transactions within the date range we care about
            Transaction.date >= date(periods[0][0], periods[0][1], 1),
        ).group_by(
            extract("year",  Transaction.date),
            extract("month", Transaction.date),
        ).all()

        # Index results by (year, month) for fast lookup
        row_map = {(int(r.yr), int(r.mo)): r for r in rows}

        month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]

        data = []
        for (y, m) in periods:
            r = row_map.get((y, m))
            income  = float(r.income  or 0) if r else 0.0
            expense = float(r.expense or 0) if r else 0.0
            data.append({
                "month":   month_names[m - 1],
                "year":    y,
                "income":  round(income, 2),
                "expense": round(expense, 2),
                "savings": round(max(0, income - expense), 2),
            })

        return data

    @staticmethod
    def get_weekly_spending(user_id):
        """
        Get spending per day for the current week.
        Single query instead of 7 separate queries.
        """
        today         = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week   = start_of_week + timedelta(days=6)        # Sunday

        rows = db.session.query(
            Transaction.date,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= start_of_week,
            Transaction.date <= end_of_week,
        ).group_by(Transaction.date).all()

        # Index by date
        day_map = {r.date: float(r.total) for r in rows}

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [
            {
                "day":      days[i],
                "date":     (start_of_week + timedelta(days=i)).isoformat(),
                "amount":   round(day_map.get(start_of_week + timedelta(days=i), 0.0), 2),
                "is_today": (start_of_week + timedelta(days=i)) == today,
            }
            for i in range(7)
        ]

    @staticmethod
    def get_smart_insights(user_id):
        """Generate financial insights. Uses SQL aggregation, not full table loads."""
        now           = datetime.now()
        curr_month    = now.month
        curr_year     = now.year
        prev_month    = curr_month - 1 or 12
        prev_year     = curr_year if curr_month > 1 else curr_year - 1

        # Single query for both months — group by (year, month, type)
        rows = db.session.query(
            extract("year",  Transaction.date).label("yr"),
            extract("month", Transaction.date).label("mo"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        ).filter(
            Transaction.user_id == user_id,
            (
                (extract("month", Transaction.date) == curr_month) &
                (extract("year",  Transaction.date) == curr_year)
            ) | (
                (extract("month", Transaction.date) == prev_month) &
                (extract("year",  Transaction.date) == prev_year)
            ),
        ).group_by(
            extract("year",  Transaction.date),
            extract("month", Transaction.date),
            Transaction.type,
        ).all()

        def key(yr, mo, typ):
            return (int(yr), int(mo), typ)

        totals = {key(r.yr, r.mo, r.type): float(r.total or 0) for r in rows}

        curr_income  = totals.get((curr_year, curr_month, "income"),  0)
        curr_expense = totals.get((curr_year, curr_month, "expense"), 0)
        prev_expense = totals.get((prev_year, prev_month, "expense"), 0)

        # Category breakdown for current month (single grouped query)
        cat_rows = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label("total"),
        ).join(Transaction, Transaction.category_id == Category.id).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            extract("month", Transaction.date) == curr_month,
            extract("year",  Transaction.date) == curr_year,
        ).group_by(Category.name).all()

        curr_by_cat = {r.name: float(r.total or 0) for r in cat_rows}

        # Previous month category breakdown
        prev_cat_rows = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label("total"),
        ).join(Transaction, Transaction.category_id == Category.id).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            extract("month", Transaction.date) == prev_month,
            extract("year",  Transaction.date) == prev_year,
        ).group_by(Category.name).all()

        prev_by_cat = {r.name: float(r.total or 0) for r in prev_cat_rows}

        insights = []

        if prev_expense > 0 and curr_expense > 0:
            change_pct = ((curr_expense - prev_expense) / prev_expense) * 100
            if change_pct > 10:
                insights.append({
                    "type": "warning", "icon": "fa-arrow-up",
                    "title": "Spending Increase",
                    "message": f"Your total expenses increased by {abs(change_pct):.1f}% compared to last month.",
                    "color": "#ef4444",
                })
            elif change_pct < -10:
                insights.append({
                    "type": "success", "icon": "fa-arrow-down",
                    "title": "Great Savings!",
                    "message": f"Your total expenses decreased by {abs(change_pct):.1f}% compared to last month. Keep it up!",
                    "color": "#22c55e",
                })

        for cat_name, curr_amt in curr_by_cat.items():
            prev_amt = prev_by_cat.get(cat_name, 0)
            if prev_amt > 0:
                cat_change = ((curr_amt - prev_amt) / prev_amt) * 100
                if cat_change > 25:
                    insights.append({
                        "type": "warning", "icon": "fa-exclamation-triangle",
                        "title": f"{cat_name} Alert",
                        "message": f"You spent {cat_change:.0f}% more on {cat_name} this month (₹{curr_amt:,.0f} vs ₹{prev_amt:,.0f}).",
                        "color": "#f59e0b",
                    })

        if curr_income > 0:
            savings      = curr_income - curr_expense
            savings_rate = (savings / curr_income) * 100
            if savings_rate >= 30:
                insights.append({
                    "type": "success", "icon": "fa-piggy-bank",
                    "title": "Excellent Savings Rate",
                    "message": f"You're saving {savings_rate:.1f}% of your income this month. Financial experts recommend 20%+.",
                    "color": "#22c55e",
                })
            elif savings_rate < 0:
                insights.append({
                    "type": "danger", "icon": "fa-fire",
                    "title": "Overspending Alert",
                    "message": f"You've spent ₹{abs(savings):,.0f} more than you earned this month. Review your expenses.",
                    "color": "#ef4444",
                })
            elif savings_rate < 10:
                insights.append({
                    "type": "warning", "icon": "fa-chart-line",
                    "title": "Low Savings Rate",
                    "message": f"Your savings rate is only {savings_rate:.1f}%. Try to target at least 20% of your income.",
                    "color": "#f59e0b",
                })

        if curr_by_cat:
            top_cat    = max(curr_by_cat, key=curr_by_cat.get)
            top_amount = curr_by_cat[top_cat]
            if curr_expense > 0:
                top_pct = (top_amount / curr_expense) * 100
                if top_pct > 40:
                    potential_saving = top_amount * 0.15
                    insights.append({
                        "type": "info", "icon": "fa-lightbulb",
                        "title": "Budget Tip",
                        "message": f"{top_cat} accounts for {top_pct:.0f}% of your spending. Reducing by 15% could save ₹{potential_saving:,.0f}.",
                        "color": "#6366f1",
                    })

        if not insights:
            insights.append({
                "type": "info", "icon": "fa-chart-bar",
                "title": "Start Tracking",
                "message": "Add your transactions to unlock personalized AI insights about your spending patterns.",
                "color": "#6366f1",
            })

        return insights
