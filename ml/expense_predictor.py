"""
Expense Predictor ML Model for FinWise.
Predicts next month's expenses and recommends budgets.
Uses Linear Regression and Random Forest Regressor.
"""
import os
import pickle
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class ExpensePredictor:
    """
    Predicts next month's total expenses based on historical data.
    Also provides budget recommendations.
    """

    def __init__(self, model_dir=None):
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(__file__), "models"
        )
        self.lr_model = LinearRegression()
        self.rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def _build_features(self, monthly_data):
        """
        Build feature matrix from monthly expense data.
        Features: month number, 3-month rolling avg, trend, year
        """
        if len(monthly_data) < 2:
            return None, None

        X, y = [], []
        for i in range(1, len(monthly_data)):
            prev = monthly_data[i - 1]
            curr = monthly_data[i]

            # Feature: [previous month expense, rolling avg, month number]
            rolling_avg = np.mean([d["expense"] for d in monthly_data[max(0, i-3):i]])
            features = [
                prev["expense"],            # Previous month expense
                rolling_avg,                # 3-month rolling average
                prev["month"],              # Previous month number
                curr["month"],              # Current month number
                prev["income"],             # Previous month income
            ]
            X.append(features)
            y.append(curr["expense"])

        return np.array(X), np.array(y)

    def train(self, monthly_data):
        """
        Train the expense prediction model.
        monthly_data: list of {"month": int, "year": int, "expense": float, "income": float}
        """
        if len(monthly_data) < 3:
            self.is_trained = False
            return False

        X, y = self._build_features(monthly_data)
        if X is None or len(X) < 2:
            self.is_trained = False
            return False

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train both models
        self.lr_model.fit(X_scaled, y)
        self.rf_model.fit(X_scaled, y)
        self.is_trained = True
        return True

    def predict_next_month(self, monthly_data):
        """
        Predict next month's expense.
        Returns predictions from both Linear Regression and Random Forest.
        """
        if not monthly_data:
            return self._default_prediction()

        # If we have enough data, train and predict
        trained = self.train(monthly_data)

        # Get latest month's data for prediction features
        latest = monthly_data[-1]
        rolling_avg = np.mean([d["expense"] for d in monthly_data[-3:]])

        # Next month number
        next_month = (latest["month"] % 12) + 1

        features = np.array([[
            latest["expense"],
            rolling_avg,
            latest["month"],
            next_month,
            latest["income"],
        ]])

        if trained:
            features_scaled = self.scaler.transform(features)
            lr_pred = max(0, float(self.lr_model.predict(features_scaled)[0]))
            rf_pred = max(0, float(self.rf_model.predict(features_scaled)[0]))
        else:
            # Fallback: use rolling average with slight increase
            lr_pred = rolling_avg * 1.05
            rf_pred = rolling_avg * 1.03

        # Ensemble: weighted average (RF is generally more accurate)
        ensemble_pred = lr_pred * 0.4 + rf_pred * 0.6

        # Calculate trend
        if len(monthly_data) >= 2:
            recent_trend = monthly_data[-1]["expense"] - monthly_data[-2]["expense"]
            trend_label = "Increasing" if recent_trend > 0 else "Decreasing" if recent_trend < 0 else "Stable"
        else:
            trend_label = "Stable"

        return {
            "linear_regression": round(lr_pred, 2),
            "random_forest": round(rf_pred, 2),
            "predicted_expense": round(ensemble_pred, 2),
            "trend": trend_label,
            "confidence": "High" if trained and len(monthly_data) >= 6 else "Medium",
            "data_points": len(monthly_data),
        }

    def recommend_budget(self, monthly_data, income=None):
        """
        Recommend an ideal monthly budget based on historical expenses.
        Follows the 50/30/20 rule: needs/wants/savings.
        """
        if not monthly_data:
            return self._default_budget_recommendation(income)

        avg_expense = np.mean([d["expense"] for d in monthly_data])
        avg_income = income or np.mean([d.get("income", avg_expense * 1.2) for d in monthly_data])

        # Predict next month's expense
        prediction = self.predict_next_month(monthly_data)
        predicted_expense = prediction["predicted_expense"]

        # 50/30/20 rule recommendations
        needs_budget = avg_income * 0.50       # 50% for needs (essentials)
        wants_budget = avg_income * 0.30       # 30% for wants (lifestyle)
        savings_budget = avg_income * 0.20     # 20% for savings

        # Recommended total budget (needs + wants = 80% of income)
        recommended_total = needs_budget + wants_budget

        # Category suggestions (as % of total expense budget)
        category_suggestions = {
            "Food & Dining": round(recommended_total * 0.20, 2),
            "Bills & Utilities": round(recommended_total * 0.15, 2),
            "Travel": round(recommended_total * 0.10, 2),
            "Shopping": round(recommended_total * 0.12, 2),
            "Medical": round(recommended_total * 0.08, 2),
            "Entertainment": round(recommended_total * 0.05, 2),
            "Education": round(recommended_total * 0.10, 2),
            "Investment": round(savings_budget, 2),
            "Others": round(recommended_total * 0.20, 2),
        }

        return {
            "recommended_budget": round(recommended_total, 2),
            "predicted_expense": round(predicted_expense, 2),
            "average_expense": round(avg_expense, 2),
            "savings_target": round(savings_budget, 2),
            "needs_budget": round(needs_budget, 2),
            "wants_budget": round(wants_budget, 2),
            "category_suggestions": category_suggestions,
            "rule": "50/30/20",
            "insight": self._generate_budget_insight(avg_expense, avg_income, predicted_expense),
        }

    def _generate_budget_insight(self, avg_expense, avg_income, predicted_expense):
        """Generate a human-readable budget insight message."""
        savings_rate = ((avg_income - avg_expense) / avg_income * 100) if avg_income > 0 else 0

        if savings_rate >= 30:
            return f"Excellent! You're saving {savings_rate:.0f}% of your income. Keep up the great work!"
        elif savings_rate >= 20:
            return f"Good job! Your {savings_rate:.0f}% savings rate meets the recommended 20% benchmark."
        elif savings_rate >= 10:
            return f"You're saving {savings_rate:.0f}%. Try to reach 20% by cutting discretionary expenses."
        elif savings_rate >= 0:
            return f"Your savings rate is low ({savings_rate:.0f}%). Review your spending and set a savings goal."
        else:
            return "You're spending more than you earn. Prioritize cutting non-essential expenses immediately."

    def _default_prediction(self):
        return {
            "linear_regression": 0,
            "random_forest": 0,
            "predicted_expense": 0,
            "trend": "No data",
            "confidence": "Low",
            "data_points": 0,
        }

    def _default_budget_recommendation(self, income=None):
        income = income or 50000  # Default ₹50,000
        return {
            "recommended_budget": round(income * 0.80, 2),
            "predicted_expense": 0,
            "average_expense": 0,
            "savings_target": round(income * 0.20, 2),
            "needs_budget": round(income * 0.50, 2),
            "wants_budget": round(income * 0.30, 2),
            "category_suggestions": {},
            "rule": "50/30/20",
            "insight": "Add transactions to get personalized budget recommendations.",
        }
