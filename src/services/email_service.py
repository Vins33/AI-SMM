# src/services/email_service.py
"""Email service using Resend API for sending verification emails."""

import secrets

import httpx

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger("email_service")

RESEND_API_URL = "https://api.resend.com/emails"


def generate_verification_token() -> str:
    """Generate a secure random verification token."""
    return secrets.token_urlsafe(32)


def _build_verification_html(username: str, verify_url: str) -> str:
    """Build HTML email body for email verification."""
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                 background-color: #0b141a; color: #e1e1e1; padding: 40px;">
      <div style="max-width: 480px; margin: 0 auto; background: #202c33; border-radius: 16px;
                  padding: 32px; text-align: center;">
        <div style="width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 16px;
                    background: linear-gradient(135deg, #34d399, #0d9488);
                    display: flex; align-items: center; justify-content: center;">
          <span style="font-size: 28px;">✉️</span>
        </div>
        <h2 style="color: #ffffff; margin-bottom: 8px;">Verifica la tua email</h2>
        <p style="color: #9ca3af; font-size: 14px; margin-bottom: 24px;">
          Ciao <strong style="color: #34d399;">{username}</strong>, clicca il pulsante qui sotto
          per verificare il tuo indirizzo email.
        </p>
        <a href="{verify_url}"
           style="display: inline-block; padding: 12px 32px;
                  background: linear-gradient(135deg, #22c55e, #0d9488);
                  color: white; text-decoration: none; border-radius: 8px;
                  font-weight: 600; font-size: 14px;">
          Verifica Email
        </a>
        <p style="color: #6b7280; font-size: 12px; margin-top: 24px;">
          Se non hai richiesto questa verifica, puoi ignorare questa email.<br>
          Il link scade tra {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} ore.
        </p>
      </div>
    </body>
    </html>
    """


def send_verification_email(email: str, username: str, token: str) -> bool:
    """Send verification email via Resend API.

    Returns True if sent successfully, False otherwise.
    Falls back to logging the verification link when RESEND_API_KEY is not set.
    """
    verify_url = f"{settings.BASE_URL}/verify-email?token={token}"

    if not settings.RESEND_API_KEY:
        logger.info(
            f"RESEND_API_KEY non configurata — link di verifica: {verify_url}",
            extra={"email": email},
        )
        return False

    html_body = _build_verification_html(username, verify_url)

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.RESEND_FROM_EMAIL,
                "to": [email],
                "subject": "Verifica il tuo indirizzo email — Financial Agent",
                "html": html_body,
            },
            timeout=10,
        )

        if response.status_code in (200, 201):
            logger.info(f"Email di verifica inviata a {email}")
            return True
        else:
            logger.error(
                f"Resend API errore {response.status_code}: {response.text} — link: {verify_url}"
            )
            return False

    except Exception as e:
        logger.error(f"Errore invio email a {email}: {e} — link: {verify_url}")
        return False
