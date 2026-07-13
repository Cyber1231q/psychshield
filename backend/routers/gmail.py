"""Gmail router — OAuth flow and inbox scanning.

Endpoints:
    GET  /api/gmail/status     — Check if Gmail is connected.
    GET  /api/gmail/connect    — Get OAuth authorization URL.
    GET  /api/gmail/callback   — Handle OAuth callback from Google.
    GET  /api/gmail/disconnect — Remove Gmail connection.
    POST /api/gmail/scan       — Pull and analyze inbox emails.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from email.utils import parseaddr

import google.auth.exceptions
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from detectors.emotion_detector import detect_emotions
from detectors.link_verifier import verify_links, verify_sender
from detectors.manipulation_detector import detect_patterns
from detectors.risk_scorer import get_trigger_scores, score_email
from integrations.gmail_integration import (
    disconnect,
    fetch_emails,
    get_auth_url,
    handle_callback,
    is_connected,
)
from models.database import get_db
from models.entities import AnalyzedEmail, AuditLog
from models.entities import AnalysisResult as DBAnalysisResult
from routers.auth import get_current_user

router = APIRouter(tags=["gmail"])
logger = logging.getLogger("psychshield")

# Matches the pattern in utils/email_sender.py — same env var, same default.
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _oauth_result_page(status: str) -> HTMLResponse:
    """Render the page the OAuth popup lands on after Google redirects back.

    The frontend's auth token lives in memory only (never localStorage), so
    a full-page navigation to Google's consent screen and back would wipe it
    and bounce the user to /login the instant they return. Running the
    consent flow in a popup avoids that: this page posts the result back to
    the opener (the still-alive main tab) and closes itself, instead of
    navigating anywhere. If there's no opener — the popup was blocked and
    Google ended up redirecting the main tab instead, or someone opened this
    URL directly — it falls back to a normal redirect.
    """
    safe_status = "connected" if status == "connected" else "error"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Gmail authorization</title></head>
<body style="font-family: system-ui, sans-serif; padding: 2rem; color: #333;">
<p>Gmail {"connected" if safe_status == "connected" else "authorization failed"} — this window should close automatically.</p>
<script>
  if (window.opener) {{
    window.opener.postMessage({{ source: "psychshield-gmail-oauth", status: "{safe_status}" }}, "{_FRONTEND_URL}");
    window.close();
  }} else {{
    window.location.href = "{_FRONTEND_URL}/analysis?gmail={safe_status}";
  }}
</script>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/gmail/status")
def gmail_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Check if the current user has connected their Gmail account."""
    email = current_user["sub"]
    return {"connected": is_connected(email, db), "email": email}


@router.get("/gmail/connect")
def gmail_connect(current_user: dict = Depends(get_current_user)) -> dict:
    """Return the Google OAuth consent URL for the user to visit."""
    email = current_user["sub"]
    return {"auth_url": get_auth_url(email)}


@router.get("/gmail/callback")
def gmail_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Receive the authorization code from Google and exchange it for tokens.

    Google redirects here after the user grants consent. The `state`
    parameter carries the PsychShield user's email so we know whose
    account to attach the tokens to. This runs inside the OAuth popup
    (see GmailConnect.jsx), so the response posts the result back to the
    main tab rather than navigating anywhere — see _oauth_result_page.
    """
    user_email = state
    if not user_email:
        raise HTTPException(status_code=400, detail="Missing state parameter — cannot identify user")

    success = handle_callback(code, user_email, db)
    if not success:
        return _oauth_result_page("error")

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=user_email,
        action=f"Gmail connected for {user_email}",
        timestamp=datetime.now(timezone.utc),
    ))
    db.commit()
    return _oauth_result_page("connected")


@router.get("/gmail/disconnect")
def gmail_disconnect(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Remove stored Gmail credentials for the current user."""
    email = current_user["sub"]
    disconnect(email, db)
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=email,
        action=f"Gmail disconnected for {email}",
        timestamp=datetime.now(timezone.utc),
    ))
    db.commit()
    return {"message": "Gmail disconnected successfully"}


@router.post("/gmail/scan")
def scan_gmail(
    max_results: int = Query(20, ge=1, le=50),
    days_back: int = Query(7, ge=1, le=90),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Pull emails from Gmail and run them through the full detection pipeline.

    Each email goes through the identical four-module pipeline used for
    pasted emails: emotion detection → manipulation patterns → link
    verification → composite risk scoring. Results are saved to the
    database so they appear in the Dashboard.

    Args:
        max_results: Number of messages to fetch (1–50).
        days_back: Only fetch messages from the last N days (1–90).
        unread_only: If true, restrict to unread inbox messages.

    Returns:
        Summary counts and per-email results sorted by risk score.

    Raises:
        400: Gmail not connected, or refresh token was revoked.
        500: Unexpected Gmail API error.
    """
    user_email = current_user["sub"]

    if not is_connected(user_email, db):
        raise HTTPException(status_code=400, detail="Gmail not connected. Use /api/gmail/connect first.")

    try:
        gmail_emails = fetch_emails(user_email, db, max_results, days_back, unread_only)
    except google.auth.exceptions.RefreshError:
        raise HTTPException(
            status_code=401,
            detail="Gmail access was revoked. Please reconnect your Gmail account.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Gmail fetch failed for %s: %s", user_email, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch emails from Gmail.")

    if not gmail_emails:
        return {"message": "No emails found in the specified date range", "total": 0, "results": []}

    results: list[dict] = []
    now = datetime.now(timezone.utc)

    for gm in gmail_emails:
        body = gm["body"]
        if not body or len(body.strip()) < 10:
            continue

        _, sender_addr = parseaddr(gm["sender"])

        emotion = detect_emotions(body)
        manipulation = detect_patterns(body)
        links = verify_links(body, sender_addr)
        # check_dns=False: Gmail's own Authentication-Results header (parsed
        # below) is a real per-message verdict and takes precedence over the
        # domain-level DNS check verify_sender() would otherwise run.
        sender_info = verify_sender(sender_addr, check_dns=False) if sender_addr else None
        if sender_info:
            sender_info = sender_info.model_copy(update={
                "spf": gm.get("spf", "UNKNOWN"),
                "dkim": gm.get("dkim", "UNKNOWN"),
                "dmarc": gm.get("dmarc", "UNKNOWN"),
            })
        risk = score_email(
            emotion,
            manipulation,
            links,
            sender=sender_info,
        )
        triggers = get_trigger_scores(emotion)

        email_id = str(uuid.uuid4())
        snippet = body[:200] + "..." if len(body) > 200 else body

        # Save to emails table (shows in Dashboard)
        db.add(AnalyzedEmail(
            id=email_id,
            user_id=user_email,
            subject=gm["subject"],
            sender=sender_addr or gm["sender"],
            risk_score=risk.finalScore,
            risk_tier=risk.tier,
            snippet=snippet,
            body=body,
            analyzed_at=now,
        ))

        # Save full analysis result (same shape as paste-mode analysis)
        sv_json = json.dumps(sender_info.model_dump(by_alias=True)) if sender_info else "{}"
        db.add(DBAnalysisResult(
            id=str(uuid.uuid4()),
            email_id=email_id,
            emotion_score=emotion.emotionScore,
            manipulation_score=manipulation.patternScore,
            link_score=links.linkScore,
            composite_score=risk.finalScore / 100,
            tier=risk.tier,
            explanation=risk.explanation,
            triggers_json=json.dumps(triggers.model_dump()),
            techniques_json=json.dumps([t.model_dump() for t in manipulation.techniques]),
            urls_json=json.dumps([u.model_dump() for u in links.urls]),
            sender_verification_json=sv_json,
            analyzed_at=now,
        ))

        results.append({
            "id": email_id,
            "gmail_id": gm["gmail_id"],
            "subject": gm["subject"],
            "sender": gm["sender"],
            "senderAddr": sender_addr,
            "date": gm["date"],
            "riskScore": risk.finalScore,
            "riskTier": risk.tier,
            "snippet": snippet,
            "scoreReason": risk.scoreReason,
            "triggers": triggers.model_dump(),
            "techniques": len(manipulation.techniques),
            "explanation": risk.explanation,
            "linkReason": links.linkReason,
        })

    results.sort(key=lambda x: x["riskScore"], reverse=True)

    high = sum(1 for r in results if r["riskTier"] == "High")
    medium = sum(1 for r in results if r["riskTier"] == "Medium")
    low = sum(1 for r in results if r["riskTier"] == "Low")

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=user_email,
        action=f"Gmail scan: {len(results)} emails analyzed — {high} HIGH, {medium} MEDIUM, {low} LOW",
        timestamp=now,
    ))
    db.commit()

    return {
        "message": f"Analyzed {len(results)} emails",
        "total": len(results),
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "results": results,
    }
