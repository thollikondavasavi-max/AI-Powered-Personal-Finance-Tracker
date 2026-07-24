"""
Category Predictor ML Model for FinWise.
Predicts the expense category from a transaction description using NLP + ML.
Uses Logistic Regression and Naive Bayes classifiers.
"""
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split


# Training data: (description, category) pairs
# This simulates what real user transaction descriptions look like
TRAINING_DATA = [
    # Food & Dining
    ("swiggy order", "Food & Dining"), ("zomato delivery", "Food & Dining"),
    ("restaurant dinner", "Food & Dining"), ("grocery store", "Food & Dining"),
    ("pizza order", "Food & Dining"), ("coffee shop", "Food & Dining"),
    ("food court lunch", "Food & Dining"), ("vegetables market", "Food & Dining"),
    ("biryani center", "Food & Dining"), ("chai tapri", "Food & Dining"),
    ("dominos pizza", "Food & Dining"), ("mcdonalds burger", "Food & Dining"),
    ("bakery items", "Food & Dining"), ("milk and bread", "Food & Dining"),
    ("dining out family", "Food & Dining"), ("hotel breakfast", "Food & Dining"),
    ("canteen lunch", "Food & Dining"), ("snacks evening", "Food & Dining"),

    # Shopping
    ("amazon purchase", "Shopping"), ("flipkart order", "Shopping"),
    ("myntra clothes", "Shopping"), ("shoes purchase", "Shopping"),
    ("shirt buy", "Shopping"), ("jeans shopping", "Shopping"),
    ("electronic gadget", "Shopping"), ("mobile accessories", "Shopping"),
    ("online shopping", "Shopping"), ("meesho order", "Shopping"),
    ("ajio fashion", "Shopping"), ("clothing store", "Shopping"),
    ("watch purchase", "Shopping"), ("gift buy", "Shopping"),

    # Travel
    ("uber ride", "Travel"), ("ola cab", "Travel"),
    ("rapido bike", "Travel"), ("metro card", "Travel"),
    ("bus ticket", "Travel"), ("flight ticket", "Travel"),
    ("train journey", "Travel"), ("irctc booking", "Travel"),
    ("makemytrip hotel", "Travel"), ("goibibo flight", "Travel"),
    ("auto rickshaw", "Travel"), ("toll payment", "Travel"),
    ("parking charges", "Travel"), ("holiday trip", "Travel"),

    # Bills & Utilities
    ("electricity bill", "Bills & Utilities"), ("water bill", "Bills & Utilities"),
    ("internet bill", "Bills & Utilities"), ("wifi recharge", "Bills & Utilities"),
    ("mobile recharge", "Bills & Utilities"), ("postpaid bill", "Bills & Utilities"),
    ("gas cylinder", "Bills & Utilities"), ("rent payment", "Bills & Utilities"),
    ("maintenance charges", "Bills & Utilities"), ("cable tv bill", "Bills & Utilities"),
    ("broadband payment", "Bills & Utilities"), ("ott subscription", "Bills & Utilities"),
    ("netflix subscription", "Bills & Utilities"), ("amazon prime", "Bills & Utilities"),

    # Medical
    ("hospital consultation", "Medical"), ("doctor visit", "Medical"),
    ("pharmacy medicine", "Medical"), ("diagnostic test", "Medical"),
    ("blood test", "Medical"), ("health checkup", "Medical"),
    ("dental treatment", "Medical"), ("eye checkup", "Medical"),
    ("medicine purchase", "Medical"), ("gym membership", "Medical"),
    ("yoga class", "Medical"), ("ayurvedic medicine", "Medical"),

    # Education
    ("college fees", "Education"), ("university tuition", "Education"),
    ("udemy course", "Education"), ("coursera subscription", "Education"),
    ("books purchase", "Education"), ("stationery items", "Education"),
    ("school fees", "Education"), ("tuition payment", "Education"),
    ("coaching institute", "Education"), ("online course", "Education"),
    ("certification exam", "Education"), ("study material", "Education"),

    # Entertainment
    ("movie ticket", "Entertainment"), ("pvr cinemas", "Entertainment"),
    ("concert tickets", "Entertainment"), ("gaming purchase", "Entertainment"),
    ("steam games", "Entertainment"), ("spotify premium", "Entertainment"),
    ("youtube premium", "Entertainment"), ("amusement park", "Entertainment"),
    ("bowling game", "Entertainment"), ("pub outing", "Entertainment"),
    ("clubbing night", "Entertainment"), ("cricket match ticket", "Entertainment"),

    # Fuel
    ("petrol fill", "Fuel"), ("diesel refill", "Fuel"),
    ("fuel station", "Fuel"), ("petrol pump", "Fuel"),
    ("cng refill", "Fuel"), ("ev charging", "Fuel"),

    # Investment
    ("mutual fund", "Investment"), ("sip investment", "Investment"),
    ("stock purchase", "Investment"), ("zerodha trading", "Investment"),
    ("fd deposit", "Investment"), ("ppf contribution", "Investment"),
    ("nps contribution", "Investment"), ("gold purchase", "Investment"),
    ("crypto investment", "Investment"), ("share market", "Investment"),

    # Others
    ("miscellaneous expense", "Others"), ("other payment", "Others"),
    ("random purchase", "Others"), ("atm withdrawal", "Others"),
]


class CategoryPredictor:
    """
    Predicts expense category from transaction description.
    Uses a TF-IDF + Logistic Regression pipeline.
    """

    def __init__(self, model_dir=None):
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(__file__), "models"
        )
        self.model_path = os.path.join(self.model_dir, "category_model.pkl")
        self.pipeline = None
        self._load_or_train()

    def _load_or_train(self):
        """Load existing model or train a new one."""
        os.makedirs(self.model_dir, exist_ok=True)

        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.pipeline = pickle.load(f)
                return
            except Exception:
                pass  # If loading fails, retrain

        self._train()

    def _train(self):
        """Train the category prediction model."""
        descriptions = [item[0] for item in TRAINING_DATA]
        categories = [item[1] for item in TRAINING_DATA]

        # Build a pipeline: TF-IDF vectorizer + Logistic Regression
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),   # Use unigrams and bigrams
                max_features=5000,
                lowercase=True,
                stop_words="english",
            )),
            ("classifier", LogisticRegression(
                max_iter=1000,
                C=1.0,
                random_state=42,
            )),
        ])

        self.pipeline.fit(descriptions, categories)

        # Save the trained model
        with open(self.model_path, "wb") as f:
            pickle.dump(self.pipeline, f)

    def predict(self, description):
        """
        Predict category for a given description.
        Returns the predicted category name and confidence score.
        """
        if not self.pipeline:
            return "Others", 0.0

        try:
            prediction = self.pipeline.predict([description])[0]
            probabilities = self.pipeline.predict_proba([description])[0]
            confidence = round(float(max(probabilities)) * 100, 1)
            return prediction, confidence
        except Exception:
            return "Others", 0.0

    def predict_top3(self, description):
        """Return top 3 predictions with confidence scores."""
        if not self.pipeline:
            return [{"category": "Others", "confidence": 0.0}]

        try:
            probabilities = self.pipeline.predict_proba([description])[0]
            classes = self.pipeline.classes_

            top_indices = np.argsort(probabilities)[::-1][:3]
            return [
                {
                    "category": classes[i],
                    "confidence": round(float(probabilities[i]) * 100, 1),
                }
                for i in top_indices
            ]
        except Exception:
            return [{"category": "Others", "confidence": 0.0}]
