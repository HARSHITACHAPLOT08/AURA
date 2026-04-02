"""
AURA — Synthetic Transaction Data Generator
Generates realistic credit card transaction data with fraud patterns.
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

def generate_transactions(n_samples: int = 10000, fraud_ratio: float = 0.05) -> pd.DataFrame:
    n_fraud = int(n_samples * fraud_ratio)
    n_legit = n_samples - n_fraud

    # ── Legitimate transactions ─────────────────────────────────────
    legit = pd.DataFrame({
        "amount":       np.random.lognormal(mean=3.5, sigma=1.2, size=n_legit).clip(1, 5000),
        "hour":         np.random.choice(range(7, 23), size=n_legit),          # business hours
        "day_of_week":  np.random.randint(0, 7, size=n_legit),
        "merchant_cat": np.random.choice([1, 2, 3, 4, 5], size=n_legit, p=[0.3,0.25,0.2,0.15,0.1]),
        "location_risk":np.random.uniform(0.0, 0.3, size=n_legit),
        "device_trust": np.random.uniform(0.6, 1.0, size=n_legit),
        "past_fraud_ct":np.random.choice([0, 1], size=n_legit, p=[0.97, 0.03]),
        "velocity_1h":  np.random.randint(1, 5, size=n_legit),
        "dist_home_km": np.random.exponential(scale=20, size=n_legit).clip(0, 300),
        "card_age_days":np.random.randint(30, 3650, size=n_legit),
        "is_online":    np.random.choice([0, 1], size=n_legit, p=[0.6, 0.4]),
        "label":        0,
    })

    # ── Fraudulent transactions ──────────────────────────────────────
    fraud = pd.DataFrame({
        "amount":       np.concatenate([
                            np.random.uniform(500, 5000, n_fraud // 2),
                            np.random.uniform(0.01, 2.0,  n_fraud - n_fraud // 2),
                        ])[:n_fraud],
        "hour":         np.random.choice(list(range(0, 6)) + list(range(22, 24)), size=n_fraud),
        "day_of_week":  np.random.randint(0, 7, size=n_fraud),
        "merchant_cat": np.random.choice([3, 4, 5], size=n_fraud, p=[0.2, 0.4, 0.4]),
        "location_risk":np.random.uniform(0.6, 1.0, size=n_fraud),
        "device_trust": np.random.uniform(0.0, 0.4, size=n_fraud),
        "past_fraud_ct":np.random.choice([0, 1, 2, 3], size=n_fraud, p=[0.4, 0.3, 0.2, 0.1]),
        "velocity_1h":  np.random.randint(5, 20, size=n_fraud),
        "dist_home_km": np.random.uniform(200, 10000, size=n_fraud),
        "card_age_days":np.random.randint(0, 90, size=n_fraud),
        "is_online":    np.random.choice([0, 1], size=n_fraud, p=[0.2, 0.8]),
        "label":        1,
    })

    df = pd.concat([legit, fraud], ignore_index=True).sample(frac=1, random_state=42)
    df["transaction_id"] = [f"TXN{str(i).zfill(6)}" for i in range(len(df))]
    return df


if __name__ == "__main__":
    out_path = Path(__file__).parent.parent / "data" / "synthetic_transactions.csv"
    out_path.parent.mkdir(exist_ok=True)
    df = generate_transactions(10000)
    df.to_csv(out_path, index=False)
    print(f"✅  Saved {len(df)} transactions → {out_path}")
    print(f"   Fraud: {df['label'].sum()} ({df['label'].mean()*100:.1f}%)")
