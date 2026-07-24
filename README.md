# FinWise – AI-Powered Personal Finance Tracker

## Description

FinWise is a full-stack personal finance management web application that helps users track income, expenses, budgets, and savings. It also provides machine learning-powered financial insights and interactive charts to help users make better financial decisions.

---

# Features

* User Registration & Login
* JWT Authentication
* Dashboard
* Income & Expense Tracking
* Budget Management
* Savings Goals
* Transaction Management (CRUD)
* Search, Filter & Sort Transactions
* CSV Export
* Interactive Charts
* Expense Category Prediction
* Monthly Expense Prediction
* Smart Budget Recommendations
* User Profile Management

---

# Tech Stack

### Frontend

* HTML5
* CSS3
* Tailwind CSS
* JavaScript
* Chart.js

### Backend

* Python
* Flask
* Flask REST APIs

### Authentication

* JWT Authentication
* bcrypt

### Database

* SQLite

### Machine Learning

* Scikit-learn
* Pandas
* NumPy

---

# Project Structure

```text
finwise/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── models/
│   ├── User.py
│   ├── Transaction.py
│   ├── Budget.py
│   └── ...
│
├── routes/
│   ├── auth.py
│   ├── dashboard.py
│   ├── transactions.py
│   ├── budget.py
│   ├── charts.py
│   ├── ai.py
│   └── profile.py
│
├── services/
│
├── ml/
│
├── utils/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── dashboard/
│   ├── transactions/
│   ├── budget/
│   ├── charts/
│   ├── ai/
│   ├── profile/
│   └── partials/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── uploads/
```

---

# Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/finwise.git

cd finwise
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python app.py
```

The application will run at:

```text
http://127.0.0.1:5000
```

---

# Environment Variables

Create a `.env` file in the project root and add:

```env
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
PORT=5000
```

## Live Demo

https://finwise.onrender.com

