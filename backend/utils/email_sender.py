"""Email sender utility — sends password reset emails via SMTP.

Uses Gmail SMTP by default. Requires an App Password:
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"
4. Set SMTP_PASSWORD in .env to that 16-character password
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("psychshield")

SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")


def is_smtp_configured() -> bool:
    """Check if SMTP credentials are set."""
    return bool(SMTP_USER and SMTP_PASSWORD)


def send_reset_email(to_email: str, reset_token: str) -> bool:
    """Send a password reset email with the reset link.

    Args:
        to_email: Recipient email address.
        reset_token: The raw (unhashed) reset token.

    Returns:
        True if sent successfully, False otherwise.
    """
    if not is_smtp_configured():
        logger.warning(
            "SMTP not configured — reset link logged to console only. "
            "Set SMTP_USER and SMTP_PASSWORD in .env to enable email delivery."
        )
        return False

    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    msg = MIMEMultipart("alternative")
    msg["From"] = f"PsychShield <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = "PsychShield — Password Reset Request"

    text_body = f"""Password Reset Request

You requested a password reset for your PsychShield account.

Click the link below to set a new password:
{reset_link}

This link expires in 15 minutes and can only be used once.

If you did not request this reset, you can safely ignore this email.
Your password will not be changed unless you click the link above.

— PsychShield Security
Caleb University, Dept. of Cybersecurity"""

    html_body = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
      <div style="text-align: center; margin-bottom: 24px;">
        <h2 style="color: #1a1a1a; margin: 0;">PsychShield</h2>
        <p style="color: #888; font-size: 13px; margin-top: 4px;">Password Reset Request</p>
      </div>
      <div style="background: #f9f9f9; border-radius: 12px; padding: 24px; border: 1px solid #e5e5e5;">
        <p style="color: #333; font-size: 14px; line-height: 1.6; margin: 0 0 16px;">
          You requested a password reset for your PsychShield account.
        </p>
        <div style="text-align: center; margin: 24px 0;">
          <a href="{reset_link}"
             style="background: #6366f1; color: white; padding: 12px 32px;
                    border-radius: 8px; text-decoration: none; font-weight: 600;
                    font-size: 14px; display: inline-block;">
            Reset Password
          </a>
        </div>
        <p style="color: #888; font-size: 12px; line-height: 1.5; margin: 16px 0 0;">
          This link expires in <strong>15 minutes</strong> and can only be used once.<br>
          If you did not request this reset, ignore this email.
        </p>
      </div>
      <p style="color: #aaa; font-size: 11px; text-align: center; margin-top: 20px;">
        PsychShield &middot; Caleb University, Dept. of Cybersecurity
      </p>
    </div>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        import ssl

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Reset email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send reset email to %s: %s", to_email, exc)
        return False
