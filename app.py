import json
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"

bundle = joblib.load(MODEL_DIR / "model.joblib")
pipeline = bundle["pipeline"]
feature_cols = bundle["feature_cols"]
medians = bundle["medians"]

with open(MODEL_DIR / "stats.json", encoding="utf-8") as f:
    STATS = json.load(f)


def build_features(payload):
    age = float(payload.get("age", medians["age"]))
    income = float(payload.get("income_lakh", medians["income_lakh"]))
    credit_score = float(payload.get("credit_score", medians["credit_score"]))
    loan_amount = float(payload.get("loan_amount_lakh", medians["loan_amount_lakh"]))
    existing_loans = float(payload.get("existing_loans", medians["existing_loans"]))

    debt_burden = round(loan_amount / income, 3) if income > 0 else 0

    if age <= 30:
        age_group = "Young"
    elif age <= 50:
        age_group = "Middle-aged"
    else:
        age_group = "Senior"

    row = {
        "age": age,
        "income_lakh": income,
        "credit_score": credit_score,
        "loan_amount_lakh": loan_amount,
        "existing_loans": existing_loans,
        "debt_burden": debt_burden,
        "age_group_Middle-aged": 1 if age_group == "Middle-aged" else 0,
        "age_group_Senior": 1 if age_group == "Senior" else 0,
    }
    df_row = pd.DataFrame([row])[feature_cols]
    return df_row, debt_burden, age_group


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def predict():
    payload = request.get_json(force=True)

    errors = {}
    try:
        if not (18 <= float(payload.get("age", 0)) <= 100):
            errors["age"] = "Age must be between 18 and 100."
    except (TypeError, ValueError):
        errors["age"] = "Enter a valid age."
    try:
        if not (300 <= float(payload.get("credit_score", 0)) <= 900):
            errors["credit_score"] = "Credit score must be between 300 and 900."
    except (TypeError, ValueError):
        errors["credit_score"] = "Enter a valid credit score."
    try:
        if float(payload.get("income_lakh", -1)) <= 0:
            errors["income_lakh"] = "Income must be greater than 0."
    except (TypeError, ValueError):
        errors["income_lakh"] = "Enter a valid income."
    try:
        if float(payload.get("loan_amount_lakh", -1)) <= 0:
            errors["loan_amount_lakh"] = "Loan amount must be greater than 0."
    except (TypeError, ValueError):
        errors["loan_amount_lakh"] = "Enter a valid loan amount."
    try:
        if float(payload.get("existing_loans", -1)) < 0:
            errors["existing_loans"] = "Existing loans cannot be negative."
    except (TypeError, ValueError):
        errors["existing_loans"] = "Enter a valid number of existing loans."

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    X_row, debt_burden, age_group = build_features(payload)
    proba_approved = float(pipeline.predict_proba(X_row)[0][1])
    decision = "APPROVED" if proba_approved >= 0.5 else "DECLINED"

    return jsonify({
        "ok": True,
        "decision": decision,
        "probability_approved": round(proba_approved, 3),
        "debt_burden": debt_burden,
        "age_group": age_group,
    })


@app.route("/api/stats")
def stats():
    return jsonify(STATS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
