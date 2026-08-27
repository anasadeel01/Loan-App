# Ledger — Credit Decision Engine

An end-to-end machine learning web application for loan approval prediction, combining a Scikit-learn classification pipeline with a Flask backend and an interactive web interface.

The application accepts applicant financial information, generates a real-time loan approval decision with probability scoring, and provides model and dataset insights through an integrated analytics dashboard.


## Overview

Ledger transforms a trained loan approval model into a functional web application.

Instead of stopping at exploratory data analysis and model training, the project takes the complete workflow from:

**Data → Cleaning → Feature Engineering → Model Training → Model Persistence → REST API → Web Interface → Real-Time Prediction**

The application uses a Logistic Regression pipeline with feature scaling and exposes the trained model through a Flask API.


## What's inside

loan_app/
├── app.py                 # Flask server: serves the UI + /api/predict + /api/stats
├── train_model.py         # Reproduces the EDA notebook's cleaning/FE pipeline, trains the model
├── 10_loan_approval.csv   # The dataset (same one used in the notebook)
├── model/
│   ├── model.joblib        # Trained sklearn pipeline (StandardScaler + LogisticRegression)
│   └── stats.json          # Precomputed dashboard stats (approval rates, coefficients, etc.)
├── templates/
│   └── index.html          # Single-page UI
└── static/
    ├── style.css            # "Ledger" design system (dark vault theme, paper form, stamp animation)
    └── script.js            # Form handling, gauge/stamp animation, Chart.js dashboard


## Key Features

- Real time loan approval prediction
- Probability based approval scoring
- Applicant financial data processing
- Automated feature engineering
- Credit score visualization
- Approval/decline decision interface
- Dataset analytics dashboard
- Approval rate analysis by credit band
- Approval rate analysis by age segment
- Model coefficient visualization
- REST API for model inference
- Persistent trained ML pipeline using Joblib
- Interactive frontend built with vanilla HTML, CSS and JavaScript


## Machine Learning Pipeline

The model development workflow includes:

1. Dataset cleaning
2. Duplicate removal
3. Invalid value handling
4. Missing value treatment using median imputation
5. Feature engineering
6. Debt burden calculation
7. Age group segmentation
8. Feature standardization
9. Logistic Regression training
10. Model evaluation
11. Model serialization with Joblib
12. Integration with a Flask inference API

The trained pipeline contains:

    text
Input Features
      ↓
Data Preprocessing
      ↓
StandardScaler
      ↓
Logistic Regression
      ↓
Approval Probability
      ↓
APPROVED / DECLINED
