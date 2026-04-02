"""
AURA — Preprocessing Pipeline
StandardScaler + SMOTE oversampling + train/test split.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

FEATURE_COLS = [
    "amount", "hour", "day_of_week", "merchant_cat",
    "location_risk", "device_trust", "past_fraud_ct",
    "velocity_1h", "dist_home_km", "card_age_days", "is_online",
]


def preprocess(df: pd.DataFrame, fit_scaler: bool = True, scaler: StandardScaler = None):
    """
    Parameters
    ----------
    df          : raw DataFrame with FEATURE_COLS + 'label'
    fit_scaler  : True → fit a new scaler; False → use provided scaler
    scaler      : pre-fitted StandardScaler (used when fit_scaler=False)

    Returns
    -------
    X_train, X_test, y_train, y_test, scaler   (or X_scaled, scaler if no label col)
    """
    X = df[FEATURE_COLS].copy()

    if "label" not in df.columns:
        # Inference mode — just scale
        if scaler is None:
            raise ValueError("Provide a fitted scaler for inference.")
        X_scaled = scaler.transform(X)
        return pd.DataFrame(X_scaled, columns=FEATURE_COLS), scaler

    y = df["label"].values

    # Scale
    if fit_scaler:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)

    X_df = pd.DataFrame(X_scaled, columns=FEATURE_COLS)

    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y, test_size=0.2, random_state=42, stratify=y
    )

    # SMOTE on training set only
    sm = SMOTE(random_state=42, k_neighbors=5)
    X_train_res, y_train_res = sm.fit_resample(X_train, y_train)

    print(f"  Train size after SMOTE: {len(X_train_res):,}  |  fraud={y_train_res.sum():,}")
    print(f"  Test  size            : {len(X_test):,}  |  fraud={y_test.sum():,}")

    return X_train_res, X_test, y_train_res, y_test, scaler
