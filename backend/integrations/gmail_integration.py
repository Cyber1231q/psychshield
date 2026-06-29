"""Gmail integration — OAuth 2.0 flow and email fetching.

Connects to a user's Gmail inbox via Google's API,
pulls emails, and returns them for analysis.
"""

import base64
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("psychshield")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uris": [
            os.getenv(
                "GOOGLE_REDIRECT_URI",
                "http://localhost:8000/api/gmail/callback",
            )
        ],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

_user_tokens: dict[str, dict] = {}


def get_auth_url(user_email: str) -> str:
    """Generate Google OAuth consent URL."""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0],
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=user_email,
    )
    return auth_url


def handle_callback(authorization_code: str, user_email: str) -> bool:
    """Exchange authorization code for access token."""
    try:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0],
        )
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        _user_tokens[user_email] = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes),
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Gmail connected for %s", user_email)
        return True
    except Exception as exc:
        logger.error("Gmail OAuth callback failed: %s", exc)
        return False


def get_user_credentials(user_email: str) -> Optional[Credentials]:
    """Get stored credentials for a user."""
    data = _user_tokens.get(user_email)
    if not data:
        return None
    return Credentials(
        token=data["token"],
        refresh_token=data.get("refresh_token"),
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )


def is_connected(user_email: str) -> bool:
    """Check if user has connected their Gmail."""
    return user_email in _user_tokens


def disconnect(user_email: str) -> bool:
    """Remove stored credentials for a user."""
    if user_email in _user_tokens:
        del _user_tokens[user_email]
        logger.info("Gmail disconnected for %s", user_email)
        return True
    return False


def _extract_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        if part.get("parts"):
            body = _extract_body(part)
            if body:
                return body

    return ""


def fetch_emails(
    user_email: str,
    max_results: int = 20,
    days_back: int = 7,
    unread_only: bool = False,
) -> list[dict]:
    """Fetch emails from user's Gmail inbox."""
    credentials = get_user_credentials(user_email)
    if not credentials:
        raise ValueError("Gmail not connected.")

    service = build("gmail", "v1", credentials=credentials)

    query_parts: list[str] = []
    if unread_only:
        query_parts.append("is:unread")
    after = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query_parts.append(f"after:{after}")

    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results, q=" ".join(query_parts), labelIds=["INBOX"])
        .execute()
    )

    emails: list[dict] = []
    for ref in results.get("messages", []):
        try:
            msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
            headers = msg.get("payload", {}).get("headers", [])

            def _hdr(name: str) -> str:
                return next((h["value"] for h in headers if h["name"].lower() == name), "")

            body = _extract_body(msg.get("payload", {})).strip()
            emails.append({
                "gmail_id": ref["id"],
                "subject": _hdr("subject") or "No Subject",
                "sender": _hdr("from") or "Unknown",
                "date": _hdr("date"),
                "reply_to": _hdr("reply-to") or None,
                "body": body,
                "snippet": msg.get("snippet", ""),
                "labels": msg.get("labelIds", []),
            })
        except Exception as exc:
            logger.warning("Failed to fetch message %s: %s", ref["id"], exc)

    logger.info("Fetched %d emails for %s", len(emails), user_email)
    return emails
