"""Gmail integration — OAuth 2.0 flow and email fetching.

Connects to a user's Gmail inbox via Google's API using the
gmail.readonly scope. Credentials are encrypted with Fernet
(AES-128-CBC) before being written to the database, so no plaintext
OAuth tokens are ever stored in SQLite.

Thesis limitations to document:
- Gmail API quota: 250 units/user/second.
  messages.list = 5 units, messages.get = 5 units each.
  Scanning 50 emails costs ~255 units — just over the per-second cap.
  Mitigation: small delay between fetches (see fetch_emails).
- Access tokens expire after 1 hour; this module auto-refreshes them
  using the stored refresh token before each API call.
- If the user revokes Gmail access in their Google Account, the refresh
  will raise google.auth.exceptions.RefreshError. The caller catches
  this and returns a 401 asking the user to reconnect.
- Fernet key rotation invalidates all stored tokens — users must
  reconnect Gmail if TOKEN_ENCRYPTION_KEY is changed.
"""

import base64
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import google.auth.exceptions
from cryptography.fernet import Fernet, InvalidToken
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from models.entities import GmailToken

logger = logging.getLogger("psychshield")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uris": [
            os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
        ],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def _get_fernet() -> Fernet:
    """Return a Fernet instance using TOKEN_ENCRYPTION_KEY from env.

    Falls back to an ephemeral key with a warning — tokens will not
    survive server restarts in that case.
    """
    raw = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not raw:
        key = Fernet.generate_key()
        logger.warning(
            "TOKEN_ENCRYPTION_KEY not set — Gmail tokens will be lost on restart. "
            "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and add it to backend/.env"
        )
        return Fernet(key)
    return Fernet(raw.encode())


def _encrypt(data: dict) -> str:
    """Serialize a dict to JSON and encrypt it with Fernet."""
    return _get_fernet().encrypt(json.dumps(data).encode()).decode()


def _decrypt(blob: str) -> dict:
    """Decrypt a Fernet blob back to a dict."""
    return json.loads(_get_fernet().decrypt(blob.encode()))


# ── Auth URL ─────────────────────────────────────────────────────

# get_auth_url() and handle_callback() are two separate HTTP requests —
# often a minute or more apart, once the user has clicked through Google's
# consent screen — so they necessarily use two separate Flow objects.
# google-auth-oauthlib auto-generates a PKCE code_verifier inside the first
# Flow when authorization_url() builds the consent URL (embedding its
# derived code_challenge), but that verifier only lives on that one Flow
# instance. Without handing it to the second Flow before fetch_token(),
# Google's token endpoint rejects the exchange with
# "(invalid_grant) Missing code verifier". A small in-memory dict keyed by
# user_email (the same value sent as the OAuth `state` param) bridges the
# two requests — adequate for this single-process deployment, same
# simplicity level as the in-memory login rate limiter in routers/auth.py.
_PENDING_CODE_VERIFIERS: dict[str, str] = {}


def get_auth_url(user_email: str) -> str:
    """Generate Google OAuth consent URL for the gmail.readonly scope.

    The user_email is passed as the OAuth state parameter so the
    callback knows which PsychShield account to associate the token with.
    """
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0],
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # always re-prompt to guarantee a refresh_token
        state=user_email,
    )
    _PENDING_CODE_VERIFIERS[user_email] = flow.code_verifier
    return auth_url


# ── OAuth callback ───────────────────────────────────────────────

def handle_callback(authorization_code: str, user_email: str, db: Session) -> bool:
    """Exchange the authorization code for tokens and store them encrypted.

    Args:
        authorization_code: The code Google returned to /api/gmail/callback.
        user_email: PsychShield user to associate these tokens with.
        db: SQLAlchemy session.

    Returns:
        True on success, False if the exchange failed.
    """
    try:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0],
        )
        flow.code_verifier = _PENDING_CODE_VERIFIERS.pop(user_email, None)
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials

        if not creds.refresh_token:
            logger.error(
                "Gmail OAuth for %s returned no refresh_token. "
                "The user may have already authorized this app — "
                "revoke access in Google Account and try again.",
                user_email,
            )
            return False

        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or SCOPES),
        }

        existing = db.query(GmailToken).filter(
            GmailToken.user_email == user_email
        ).first()

        if existing:
            existing.encrypted_blob = _encrypt(token_data)
            existing.connected_at = datetime.now(timezone.utc)
        else:
            db.add(GmailToken(
                id=str(uuid.uuid4()),
                user_email=user_email,
                encrypted_blob=_encrypt(token_data),
                connected_at=datetime.now(timezone.utc),
            ))

        db.commit()
        logger.info("Gmail credentials stored (encrypted) for %s", user_email)
        return True

    except Exception as exc:
        logger.error("Gmail OAuth callback failed for %s: %s", user_email, exc)
        return False


# ── Credential retrieval + auto-refresh ─────────────────────────

def _load_and_refresh(user_email: str, db: Session) -> Optional[Credentials]:
    """Load stored credentials, refresh if expired, persist updated token.

    Returns None if no credentials are stored or decryption fails.
    Raises google.auth.exceptions.RefreshError if the refresh token
    has been revoked by the user.
    """
    row = db.query(GmailToken).filter(GmailToken.user_email == user_email).first()
    if not row:
        return None

    try:
        data = _decrypt(row.encrypted_blob)
    except (InvalidToken, Exception) as exc:
        logger.error("Failed to decrypt Gmail token for %s: %s", user_email, exc)
        return None

    creds = Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )

    if not creds.valid:
        if creds.refresh_token:
            creds.refresh(Request())
            # Persist the new access token so we don't refresh on every call
            data["token"] = creds.token
            row.encrypted_blob = _encrypt(data)
            row.last_used = datetime.now(timezone.utc)
            db.commit()
            logger.debug("Gmail access token refreshed for %s", user_email)
        else:
            logger.error("Gmail credentials for %s are invalid and have no refresh token", user_email)
            return None
    else:
        row.last_used = datetime.now(timezone.utc)
        db.commit()

    return creds


# ── Status helpers ───────────────────────────────────────────────

def is_connected(user_email: str, db: Session) -> bool:
    """Return True if the user has stored Gmail credentials."""
    return db.query(GmailToken).filter(
        GmailToken.user_email == user_email
    ).first() is not None


def disconnect(user_email: str, db: Session) -> bool:
    """Delete stored Gmail credentials for a user."""
    row = db.query(GmailToken).filter(GmailToken.user_email == user_email).first()
    if row:
        db.delete(row)
        db.commit()
        logger.info("Gmail credentials deleted for %s", user_email)
        return True
    return False


# ── Email body extraction ────────────────────────────────────────

def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime = payload.get("mimeType", "")

    if mime == "text/plain":
        raw = payload.get("body", {}).get("data", "")
        if raw:
            return base64.urlsafe_b64decode(raw + "==").decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            raw = part.get("body", {}).get("data", "")
            if raw:
                return base64.urlsafe_b64decode(raw + "==").decode("utf-8", errors="ignore")
        nested = _extract_body(part)
        if nested:
            return nested

    return ""


# ── Authentication verdict parsing ───────────────────────────────

_AUTH_VERDICT_MAP = {"pass": "PASS", "fail": "FAIL", "softfail": "FAIL"}


def _parse_google_auth_results(headers: list[dict]) -> dict:
    """Extract real SPF/DKIM/DMARC verdicts from Gmail's own Authentication-Results header.

    Gmail — like other major providers — strips any Authentication-Results
    header a message arrived with and re-stamps its own at the trust
    boundary, so only a header whose authserv-id is a *.google.com host
    can be trusted; anything else could have been forged by the sender
    before it ever reached Google. Returns UNKNOWN for any verdict that
    can't be confirmed this way (e.g. neutral/none/temperror/permerror,
    or no trustworthy header present at all).
    """
    result = {"spf": "UNKNOWN", "dkim": "UNKNOWN", "dmarc": "UNKNOWN"}
    for h in headers:
        if h.get("name", "").lower() != "authentication-results":
            continue
        value = h.get("value", "")
        authserv_id = value.split(";", 1)[0].strip().lower()
        if "google.com" not in authserv_id:
            continue
        for key in ("spf", "dkim", "dmarc"):
            match = re.search(rf"\b{key}=(\w+)", value, re.IGNORECASE)
            if match:
                result[key] = _AUTH_VERDICT_MAP.get(match.group(1).lower(), "UNKNOWN")
    return result


# ── Inbox fetch ──────────────────────────────────────────────────

def fetch_emails(
    user_email: str,
    db: Session,
    max_results: int = 20,
    days_back: int = 7,
    unread_only: bool = False,
) -> list[dict]:
    """Fetch emails from the user's Gmail inbox.

    Quota note: messages.list = 5 units, messages.get = 5 units each.
    max_results=20 → ~105 units; max_results=50 → ~255 units (at limit).
    A 50ms sleep between individual message fetches keeps burst usage
    safely under the 250 units/second cap.

    Args:
        user_email: PsychShield user whose inbox to read.
        db: SQLAlchemy session (needed for token refresh persistence).
        max_results: How many messages to fetch (1–50).
        days_back: Only fetch emails received within this many days.
        unread_only: If True, restrict to unread messages.

    Returns:
        List of dicts with gmail_id, subject, sender, date, body, etc.

    Raises:
        ValueError: Gmail not connected.
        google.auth.exceptions.RefreshError: Refresh token revoked.
        HttpError: Gmail API returned a non-2xx response.
    """
    creds = _load_and_refresh(user_email, db)
    if not creds:
        raise ValueError("Gmail not connected — no valid credentials found.")

    service = build("gmail", "v1", credentials=creds)

    query_parts: list[str] = []
    if unread_only:
        query_parts.append("is:unread")
    after = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query_parts.append(f"after:{after}")

    list_response = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=max_results,
            q=" ".join(query_parts),
            labelIds=["INBOX"],
        )
        .execute()
    )

    emails: list[dict] = []
    for ref in list_response.get("messages", []):
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=ref["id"], format="full")
                .execute()
            )
            headers = msg.get("payload", {}).get("headers", [])

            def _hdr(name: str) -> str:
                return next(
                    (h["value"] for h in headers if h["name"].lower() == name), ""
                )

            body = _extract_body(msg.get("payload", {})).strip()
            auth = _parse_google_auth_results(headers)
            emails.append({
                "gmail_id": ref["id"],
                "subject": _hdr("subject") or "No Subject",
                "sender": _hdr("from") or "Unknown",
                "date": _hdr("date"),
                "reply_to": _hdr("reply-to") or None,
                "body": body,
                "snippet": msg.get("snippet", ""),
                "labels": msg.get("labelIds", []),
                "spf": auth["spf"],
                "dkim": auth["dkim"],
                "dmarc": auth["dmarc"],
            })
            # Throttle to stay under 250 quota units/second
            time.sleep(0.05)

        except HttpError as exc:
            logger.warning("Failed to fetch Gmail message %s: %s", ref["id"], exc)

    logger.info("Fetched %d emails for %s", len(emails), user_email)
    return emails
