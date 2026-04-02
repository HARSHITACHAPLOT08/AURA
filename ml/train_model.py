"""
AURA — Model Training Script
Trains XGBoost (primary) + Isolation Forest (anomaly backup).
Saves models + scaler + SHAP explainer to /models/
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import joblib
import shap
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report, roc_auc_score,
    confusion_matrix, average_precision_score,
)

from ml.generate_synthetic import generate_transactions
from ml.preprocess import preprocess, FEATURE_COLS

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def train():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  AURA — Model Training Pipeline")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 1. Generate / load data
    data_path = DATA_DIR / "synthetic_transactions.csv"
    if data_path.exists():
        df = pd.read_csv(data_path)
        print(f"✅  Loaded existing data: {len(df):,} rows")
    else:
        df = generate_transactions(12000)
        df.to_csv(data_path, index=False)
        print(f"✅  Generated data: {len(df):,} rows")

    # 2. Preprocess
    print("\n📊  Preprocessing …")
    X_train, X_test, y_train, y_test, scaler = preprocess(df)
    joblib.dump(scaler, MODELS_DIR / "scaler.pkl")
    print(f"  Saved scaler → {MODELS_DIR / 'scaler.pkl'}")

    # 3. XGBoost
    print("\n🤖  Training XGBoost …")
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=20,        # handle class imbalance
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )
    xgb.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50,
    )
    joblib.dump(xgb, MODELS_DIR / "xgboost_model.pkl")

    y_prob = xgb.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    roc    = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    print("\n📈  XGBoost Metrics:")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))
    print(f"  ROC-AUC : {roc:.4f}")
    print(f"  PR-AUC  : {pr_auc:.4f}")
    print(f"  Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    # 4. Isolation Forest (anomaly layer)
    print("\n🌲  Training Isolation Forest …")
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_train[y_train == 0])   # fit on legit only
    joblib.dump(iso, MODELS_DIR / "isolation_forest.pkl")

    # 5. SHAP Explainer
    print("\n🔍  Building SHAP explainer …")
    explainer = shap.TreeExplainer(xgb)
    # Compute sample SHAP values and save feature importance
    sample = X_test.sample(min(200, len(X_test)), random_state=42)
    shap_output = explainer.shap_values(sample)
    # shap_output may be a 2D array (binary classification) or list of 2 arrays
    if isinstance(shap_output, list):
        shap_vals = shap_output[1]  # positive class
    else:
        shap_vals = shap_output
    mean_abs  = np.abs(shap_vals).mean(axis=0)
    importance = {f: float(v) for f, v in zip(FEATURE_COLS, mean_abs)}

    with open(MODELS_DIR / "feature_importance.json", "w") as fh:
        json.dump(importance, fh, indent=2)

    # Save the explainer
    joblib.dump(explainer, MODELS_DIR / "shap_explainer.pkl")

    print("\n✅  All models saved to /models/")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Training complete!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    train()
