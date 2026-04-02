# AURA — AI-Powered Real-Time Fraud Detection & Financial Guardian System

<div align="center">

```
    ██████╗  █████╗ ██╗   ██╗██████╗  █████╗
   ██╔══██╗██╔══██╗██║   ██║██╔══██╗██╔══██╗
   ███████║██║  ╚═╝██║   ██║██████╔╝███████║
   ██╔══██║██║  ██╗██║   ██║██╔══██╗██╔══██║
   ██║  ██║╚█████╔╝╚██████╔╝██║  ██║██║  ██║
   ╚═╝  ╚═╝ ╚════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
```

**AI-Powered Real-Time Fraud Detection & Financial Guardian System**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange)
![SHAP](https://img.shields.io/badge/XAI-SHAP-purple)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **XGBoost + Isolation Forest** | Dual-model fraud detection with blended scoring |
| 🔍 **SHAP Explainability** | Per-transaction AI explanations — know WHY it flagged |
| 🎯 **Risk Score Gauge** | Visual 0–100% fraud probability meter |
| ⚡ **Real-Time Streaming** | Auto-simulate transaction streams with live detection |
| 🔐 **Cyber Awareness Hub** | Phishing demos, safe/unsafe patterns, security tips |
| 📊 **Analytics Dashboard** | Charts for fraud trends, hourly patterns, feature importance |
| 💾 **SQLite Storage** | All transactions persisted automatically |
| 🌐 **FastAPI Backend** | Optional REST API for integration |

---

## 📁 Project Structure

```
AI_Fraud_Detection/
├── app/
│   └── main.py                  ← Streamlit dashboard (main UI)
├── backend/
│   ├── api.py                   ← FastAPI REST API
│   ├── model_engine.py          ← ML inference + SHAP
│   ├── alert_system.py          ← Recommendations + phishing examples
│   └── database.py              ← SQLite persistence
├── ml/
│   ├── train_model.py           ← Training script (XGBoost + IF)
│   ├── preprocess.py            ← Scaling + SMOTE
│   └── generate_synthetic.py   ← Synthetic data generator
├── models/                      ← Saved models (auto-generated)
├── data/                        ← CSV + SQLite database
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the Models

```bash
python ml/train_model.py
```

This will:
- Generate 12,000 synthetic transactions
- Apply SMOTE oversampling
- Train XGBoost + Isolation Forest
- Save models + SHAP explainer to `/models/`

### 3. Launch the Dashboard

```bash
streamlit run app/main.py
```

Open http://localhost:8501 in your browser.

### 4. (Optional) Start the FastAPI Backend

```bash
uvicorn backend.api:app --reload --port 8000
```

API docs at http://localhost:8000/docs

---

## 🧠 ML Pipeline

```
Raw Transaction
      ↓
StandardScaler (feature normalization)
      ↓
XGBoost Classifier  ──┐
                       ├─→ Blended Score (80/20)
Isolation Forest    ──┘
      ↓
SHAP Explanation (per-feature contributions)
      ↓
Risk Level: Low / Medium / High
      ↓
Alert System + Recommendations
      ↓
SQLite Storage + Dashboard Display
```

---

## 🎯 Transaction Features

| Feature | Description |
|---|---|
| `amount` | Transaction amount (₹) |
| `hour` | Hour of transaction (0-23) |
| `day_of_week` | Day number (0=Mon, 6=Sun) |
| `merchant_cat` | Category (1=Groceries … 5=Luxury) |
| `location_risk` | Geographic risk score (0-1) |
| `device_trust` | Device trust score (0-1) |
| `past_fraud_ct` | Number of previous fraud flags |
| `velocity_1h` | Transactions in past 1 hour |
| `dist_home_km` | Distance from home location |
| `card_age_days` | Age of card used |
| `is_online` | Online vs in-person transaction |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | System health + model status |
| POST | `/predict` | Predict fraud on a transaction |
| GET | `/stream-next` | Fetch + analyze a random transaction |
| GET | `/history` | Recent transaction history |
| GET | `/stats` | Aggregate fraud statistics |

---

## 🔐 Cybersecurity Awareness

AURA includes a dedicated **Cyber Awareness Hub** with:
- 4 real-world phishing attack simulations (SMS, email, vishing, QR)
- Safe vs unsafe transaction pattern comparison
- Interactive security quiz
- 8 essential security practice cards
- Links to RBI, CERT-In, Cyber Crime Portal

---

## 🏆 Tech Stack

- **ML**: XGBoost, Scikit-learn, Imbalanced-learn (SMOTE), SHAP
- **UI**: Streamlit with custom dark-theme CSS, Plotly charts
- **API**: FastAPI + Uvicorn
- **DB**: SQLite via SQLAlchemy
- **Data**: Synthetic fraud dataset (no Kaggle account needed)

---

> Built for hackathons · Demo-ready · AURA v1.0
