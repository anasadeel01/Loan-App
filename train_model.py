"""
Reproduces the exact cleaning + feature engineering pipeline from
Loan_Approval_EDA_FE.ipynb, then trains a simple Logistic Regression
classifier and exports:
  - model/model.joblib      (trained sklearn pipeline)
  - model/stats.json        (dashboard stats for the frontend)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "10_loan_approval.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)

numeric_cols = ["age", "income_lakh", "credit_score", "loan_amount_lakh", "existing_loans"]

df_clean = df.copy()
df_clean = df_clean.drop_duplicates()
df_clean = df_clean[df_clean["approved"].isin([0, 1])]

df_clean.loc[(df_clean["age"] < 18) | (df_clean["age"] > 100), "age"] = np.nan
df_clean.loc[(df_clean["credit_score"] < 300) | (df_clean["credit_score"] > 900), "credit_score"] = np.nan
df_clean.loc[df_clean["income_lakh"] < 0, "income_lakh"] = np.nan
df_clean.loc[df_clean["existing_loans"] < 0, "existing_loans"] = np.nan

medians = {}
for col in numeric_cols:
    medians[col] = float(df_clean[col].median())
    df_clean[col] = df_clean[col].fillna(medians[col])

df_clean["approved"] = df_clean["approved"].astype(int)

# ---- Feature engineering (same as notebook) ----
df_clean["debt_burden"] = (df_clean["loan_amount_lakh"] / df_clean["income_lakh"]).round(3)
df_clean["age_group"] = pd.cut(
    df_clean["age"], bins=[0, 30, 50, 200], labels=["Young", "Middle-aged", "Senior"]
)

df_model = pd.get_dummies(df_clean, columns=["age_group"], drop_first=True)

feature_cols = [c for c in df_model.columns if c != "approved"]
X = df_model[feature_cols]
y = df_model["approved"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000))
])
pipe.fit(X_train, y_train)

y_pred = pipe.predict(X_test)
y_proba = pipe.predict_proba(X_test)[:, 1]
acc = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)
print(f"Test accuracy: {acc:.3f} | ROC-AUC: {auc:.3f}")

joblib.dump({"pipeline": pipe, "feature_cols": feature_cols, "medians": medians}, MODEL_DIR / "model.joblib")

# ---- Dashboard stats for the frontend ----
approval_rate = float(df_clean["approved"].mean())

by_age_group = (
    df_clean.groupby("age_group", observed=True)["approved"]
    .mean()
    .reindex(["Young", "Middle-aged", "Senior"])
    .round(3)
    .fillna(0)
    .to_dict()
)

# bucket credit score and average approval rate per bucket (for a chart)
bins = [300, 500, 600, 650, 700, 750, 800, 900]
labels = ["300-500", "500-600", "600-650", "650-700", "700-750", "750-800", "800-900"]
df_clean["credit_bucket"] = pd.cut(df_clean["credit_score"], bins=bins, labels=labels, include_lowest=True)
by_credit_bucket = (
    df_clean.groupby("credit_bucket", observed=True)["approved"]
    .mean()
    .reindex(labels)
    .round(3)
    .fillna(0)
    .to_dict()
)

corr = df_clean[numeric_cols + ["debt_burden", "approved"]].corr()["approved"].drop("approved").round(3).to_dict()

coefs = dict(zip(feature_cols, pipe.named_steps["clf"].coef_[0].round(3).tolist()))

stats = {
    "n_rows_raw": int(len(df)),
    "n_rows_clean": int(len(df_clean)),
    "duplicates_removed": int(len(df) - len(df.drop_duplicates())),
    "approval_rate": round(approval_rate, 3),
    "by_age_group": by_age_group,
    "by_credit_bucket": by_credit_bucket,
    "correlation_with_approval": corr,
    "model_coefficients": coefs,
    "test_accuracy": round(float(acc), 3),
    "test_auc": round(float(auc), 3),
    "medians": medians,
}

with open(MODEL_DIR / "stats.json", "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2)

print("Model + stats exported.")
print(json.dumps(stats, indent=2))
