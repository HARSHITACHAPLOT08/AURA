"""
AURA — FastAPI Backend
Endpoints: /predict  /history  /stats  /stream-next
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import uuid

from backend.model_engine import predict, models_ready
from backend.database     import save_transaction, get_recent_transactions, get_stats
from backend.alert_system import get_recommendations
from ml.generate_synthetic import generate_transactions

app = FastAPI(
    title="AURA Fraud Detection API",
    description="AI-Powered Real-Time Fraud Detection & Financial Guardian System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Synthetic pool for streaming
_stream_pool = None


def _get_stream_pool():
    global _stream_pool
    if _stream_pool is None:
        df = generate_transactions(n_samples=500)
        _stream_pool = df.to_dict(orient="records")
    return _stream_pool


# ── Schemas ─────────────────────────────────────────────────────────
class TransactionInput(BaseModel):
    amount:        float = Field(..., gt=0)
    hour:          int   = Field(..., ge=0, le=23)
    day_of_week:   int   = Field(..., ge=0, le=6)
    merchant_cat:  int   = Field(..., ge=1, le=5)
    location_risk: float = Field(..., ge=0, le=1)
    device_trust:  float = Field(..., ge=0, le=1)
    past_fraud_ct: int   = Field(..., ge=0)
    velocity_1h:   int   = Field(..., ge=0)
    dist_home_km:  float = Field(..., ge=0)
    card_age_days: int   = Field(..., ge=0)
    is_online:     bool  = False
    source:        str   = "manual"


# ── Routes ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "models_ready": models_ready()}


@app.post("/predict")
def predict_fraud(tx: TransactionInput):
    if not models_ready():
        raise HTTPException(503, detail="Models not trained yet. Run ml/train_model.py first.")
    data = tx.model_dump()
    data["transaction_id"] = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    result = predict(data)
    save_transaction(result)
    recs = get_recommendations(result["risk_level"], data)
    return {**result, "recommendations": recs}


@app.get("/stream-next")
def stream_next():
    """Return one random transaction from the synthetic pool + run inference."""
    if not models_ready():
        raise HTTPException(503, detail="Models not trained yet.")
    pool = _get_stream_pool()
    import random
    tx   = random.choice(pool)
    tx["transaction_id"] = f"STR-{uuid.uuid4().hex[:8].upper()}"
    tx["source"] = "stream"
    result = predict(tx)
    save_transaction(result)
    return result


@app.get("/history")
def history(limit: int = 50):
    return get_recent_transactions(limit)


@app.get("/stats")
def stats():
    return get_stats()


if __name__ == "__main__":
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
