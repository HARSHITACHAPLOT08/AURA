"""
AURA — Database Layer
SQLite via SQLAlchemy for transaction history, user profiles and KYC storage.
"""
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    Boolean, DateTime, Text, inspect,
)
from sqlalchemy.orm import declarative_base, sessionmaker

"""
AURA — Database Layer
SQLite via SQLAlchemy for transaction history, user profiles and KYC storage.
"""
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    Boolean, DateTime, Text, inspect,
)
from sqlalchemy.orm import declarative_base, sessionmaker


# Streamlit Cloud / Docker: only /tmp is writable. Local dev: use data/ folder.
def _resolve_db_path() -> Path:
    local_data = Path(__file__).parent.parent / "data"
    try:
        local_data.mkdir(exist_ok=True)
        test = local_data / ".write_test"
        test.touch(); test.unlink()
        return local_data / "aura.db"
    except OSError:
        return Path("/tmp") / "aura.db"


DB_PATH = _resolve_db_path()
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    hour = Column(Integer)
    day_of_week = Column(Integer)
    merchant_cat = Column(Integer)
    location_risk = Column(Float)
    device_trust = Column(Float)
    past_fraud_ct = Column(Integer)
    velocity_1h = Column(Integer)
    dist_home_km = Column(Float)
    card_age_days = Column(Integer)
    is_online = Column(Boolean)

    fraud_probability = Column(Float)
    risk_level = Column(String)    # Low / Medium / High
    is_fraud = Column(Boolean)
    anomaly_score = Column(Float)
    top_features = Column(Text)      # JSON string

    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String, default="manual")  # manual | stream


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    settings = Column(Text, nullable=True)       # JSON string for arbitrary settings
    kyc_status = Column(String, default="not_submitted")
    kyc_document = Column(String, nullable=True)  # path to uploaded document
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=ENGINE)


def save_transaction(data: dict, db=None):
    """Persist a prediction result to the DB."""
    close = False
    if db is None:
        db = SessionLocal()
        close = True
    try:
        row_data = dict(data)
        ts = row_data.get("timestamp")
        if isinstance(ts, str):
            try:
                row_data["timestamp"] = datetime.fromisoformat(ts)
            except ValueError:
                row_data["timestamp"] = datetime.utcnow()
        elif ts is None:
            row_data["timestamp"] = datetime.utcnow()

        row = Transaction(**row_data)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        if close:
            db.close()


def get_recent_transactions(limit: int = 100) -> list:
    db = SessionLocal()
    try:
        rows = db.query(Transaction).order_by(Transaction.id.desc()).limit(limit).all()
        return [_row_to_dict(r) for r in rows]
    finally:
        db.close()


def get_stats() -> dict:
    db = SessionLocal()
    try:
        total = db.query(Transaction).count()
        fraud = db.query(Transaction).filter(Transaction.is_fraud == True).count()
        return {
            "total": total,
            "fraud": fraud,
            "legit": total - fraud,
            "fraud_rate": round(fraud / total * 100, 2) if total else 0.0,
        }
    finally:
        db.close()


def _row_to_dict(row: Transaction) -> dict:
    return {c.key: getattr(row, c.key) for c in inspect(row).mapper.column_attrs}


# -------------------- User / KYC helpers --------------------
def _user_to_dict(row: User) -> dict:
    if row is None:
        return None
    return {c.key: getattr(row, c.key) for c in inspect(row).mapper.column_attrs}


def get_user(username: str) -> dict:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return _user_to_dict(user)
    finally:
        db.close()


def upsert_user(profile: dict) -> dict:
    """Insert or update user profile. Requires `username` in profile."""
    if "username" not in profile:
        raise ValueError("username is required")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == profile["username"]).first()
        if user is None:
            user = User(username=profile["username"],
                        full_name=profile.get("full_name"),
                        email=profile.get("email"),
                        phone=profile.get("phone"),
                        settings=profile.get("settings"),
                        kyc_status=profile.get("kyc_status", "not_submitted"),
                        kyc_document=profile.get("kyc_document"))
            db.add(user)
        else:
            if "full_name" in profile: user.full_name = profile.get("full_name")
            if "email" in profile: user.email = profile.get("email")
            if "phone" in profile: user.phone = profile.get("phone")
            if "settings" in profile: user.settings = profile.get("settings")
            if "kyc_status" in profile: user.kyc_status = profile.get("kyc_status")
            if "kyc_document" in profile: user.kyc_document = profile.get("kyc_document")
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return _user_to_dict(user)
    finally:
        db.close()


def save_kyc(username: str, file_bytes: bytes, filename: str) -> str:
    """Save uploaded KYC document to data/uploads and update user record.
    Returns the saved path.
    """
    upl_dir = Path(__file__).parent.parent / "data" / "uploads"
    upl_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{username}_{uuid4_short()}_{os.path.basename(filename)}"
    out_path = upl_dir / safe_name
    with open(out_path, "wb") as f:
        f.write(file_bytes)

    rel_path = str(out_path)
    try:
        upsert_user({"username": username, "kyc_status": "submitted", "kyc_document": rel_path})
    except Exception:
        pass
    return rel_path


def uuid4_short():
    import uuid
    return uuid.uuid4().hex[:8]


# Initialize DB on import
init_db()
