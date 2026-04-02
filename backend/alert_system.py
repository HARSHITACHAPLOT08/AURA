"""
AURA — Alert & Cybersecurity Recommendation System
Generates contextual alerts, security tips, and phishing awareness.
"""
from typing import Optional


PHISHING_EXAMPLES = [
    {
        "type":    "SMS Phishing (Smishing)",
        "color":   "#FF4B4B",
        "message": "ALERT: Your bank account has been compromised. Click here immediately to verify: http://secure-bank-login.xyz/verify",
        "red_flags": ["Urgency language", "Unknown URL domain", "Requests click-through", "Generic greeting"],
    },
    {
        "type":    "Email Phishing",
        "color":   "#FF6B35",
        "message": "Dear Customer, We noticed unusual activity on your account. Please confirm your details at: http://bankofamerica.security-update.com",
        "red_flags": ["Suspicious subdomain (not real bank URL)", "Urgency", "'Confirm details' = credential theft", "No personal name"],
    },
    {
        "type":    "Vishing (Voice Call)",
        "color":   "#FFA500",
        "message": "This is your bank's fraud department. We detected a $4,200 transaction. Please verify your card number and PIN to cancel it.",
        "red_flags": ["Banks NEVER ask for PIN", "Unsolicited call", "High-pressure tactic", "Requests sensitive info"],
    },
    {
        "type":    "QR Code Scam",
        "color":   "#FFD700",
        "message": "Scan this QR code to claim your $500 cashback reward. Offer expires in 10 minutes!",
        "red_flags": ["Too-good-to-be-true offer", "Time pressure", "QR hides real URL", "No official branding"],
    },
]

SAFE_PATTERNS = [
    "✅ Transaction initiated from your registered device",
    "✅ Amount within your usual spending range",
    "✅ Merchant recognized from past transactions",
    "✅ Location matches your recent GPS activity",
    "✅ Card chip/contactless used (not manual entry)",
]

UNSAFE_PATTERNS = [
    "🚨 Transaction from new/unrecognized device",
    "🚨 Amount 10× higher than your average",
    "🚨 Foreign merchant category at 3 AM",
    "🚨 Card number manually keyed (no chip)",
    "🚨 Multiple transactions in < 2 minutes",
]


def get_recommendations(risk_level: str, transaction: dict) -> dict:
    """
    Returns actionable security recommendations based on risk level.
    """
    immediate_actions = []
    security_tips     = []
    watch_factors     = []

    # Risk-based recommendations
    if risk_level == "High":
        immediate_actions = [
            "🛑 **Block your card immediately** via your banking app",
            "📞 **Call your bank's fraud hotline** (number on back of card)",
            "🔐 **Change your online banking password** now",
            "📱 **Enable 2-Factor Authentication** on all accounts",
            "📧 **Check for unauthorized email changes** on linked accounts",
        ]
        security_tips = [
            "Do NOT click any links from unknown senders about this transaction",
            "Report this to your national fraud reporting center",
            "Monitor all linked accounts for the next 30 days",
            "Consider placing a credit freeze at credit bureaus",
        ]
    elif risk_level == "Medium":
        immediate_actions = [
            "⚠️ **Verify this transaction** in your banking app",
            "🔔 **Set up transaction alerts** for all future transactions",
            "🔑 **Review active sessions** in your banking account",
        ]
        security_tips = [
            "Enable biometric authentication on your banking app",
            "Avoid using public Wi-Fi for banking transactions",
            "Check if your email has been in any data breaches (haveibeenpwned.com)",
        ]
    else:
        security_tips = [
            "Enable spending notifications to monitor your card",
            "Review your monthly statement regularly",
            "Use virtual card numbers for online shopping",
        ]

    # Transaction-specific watches
    if transaction.get("is_online"):
        watch_factors.append("🌐 Online transaction — verify merchant SSL certificate")
    if transaction.get("location_risk", 0) > 0.7:
        watch_factors.append("📍 High-risk location detected")
    if transaction.get("velocity_1h", 0) > 5:
        watch_factors.append(f"⚡ High transaction velocity: {transaction.get('velocity_1h')} in 1 hour")
    if transaction.get("dist_home_km", 0) > 500:
        watch_factors.append(f"🗺️ Transaction {transaction.get('dist_home_km', 0):.0f}km from home location")
    if transaction.get("device_trust", 1) < 0.3:
        watch_factors.append("📱 Unrecognized / low-trust device")

    return {
        "risk_level":       risk_level,
        "immediate_actions": immediate_actions,
        "security_tips":    security_tips,
        "watch_factors":    watch_factors,
        "phishing_alert":   risk_level in ("Medium", "High"),
    }


def get_phishing_examples() -> list:
    return PHISHING_EXAMPLES


def get_pattern_comparison() -> dict:
    return {"safe": SAFE_PATTERNS, "unsafe": UNSAFE_PATTERNS}
