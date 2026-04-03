import os
import smtplib
from email.message import EmailMessage


def send_email_notification(to_email: str, subject: str, body: str) -> (bool, str):
    """Send a simple email notification using SMTP environment vars.

    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
    Returns (success, message).
    """
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    from_email = os.environ.get("FROM_EMAIL") or user

    if not (host and user and password and from_email):
        return False, "SMTP not configured"

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(msg)

        return True, "Sent"
    except Exception as e:
        return False, str(e)
