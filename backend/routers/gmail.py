"""Gmail router — OAuth flow and inbox scanning.

Endpoints:
    GET  /api/gmail/status     — Check if Gmail is connected.
    GET  /api/gmail/connect    — Get OAuth authorization URL.
    GET  /api/gmail/callback   — Handle OAuth callback from Google.
    GET  /api/gmail/disconnect — Remove Gmail connection.
    POST /api/gmail/scan       — Pull and analyze inbox emails.
"""

import logging
import uuid
from datetime import datetime, timezone
from email.utils import parseaddr

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
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
from routers.auth import get_current_user

router = APIRouter(tags=["gmail"])
logger = logging.getLogger("psychshield")


@router.get("/gmail/status")
def gmail_status(current_user: dict = Depends(get_current_user)) -> dict:
    """Check if user has connected their Gmail."""
    email = current_user.get("sub", "")
    return {"connected": is_connected(email), "email": email}


@router.get("/gmail/connect")
def gmail_connect(current_user: dict = Depends(get_current_user)) -> dict:
    """Get Google OAuth authorization URL."""
    email = current_user.get("sub", "")
    return {"auth_url": get_auth_url(email)}


@router.get("/gmail/callback")
def gmail_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Handle Google OAuth callback."""
    if not handle_callback(code, state):
        raise HTTPException(status_code=400, detail="Gmail authorization failed")
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=state,
        action=f"Gmail connected for {state}",
        timestamp=datetime.now(timezone.utc),
    ))
    db.commit()
    return RedirectResponse(url="http://localhost:5173/dashboard?gmail=connected")


@router.get("/gmail/disconnect")
def gmail_disconnect(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Disconnect Gmail integration."""
    email = current_user.get("sub", "")
    disconnect(email)
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
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Pull emails from Gmail and run them through the detection pipeline."""
    user_email = current_user.get("sub", "")

    if not is_connected(user_email):
        raise HTTPException(status_code=400, detail="Gmail not connected.")

    gmail_emails = fetch_emails(user_email, max_results, days_back, unread_only)
    if not gmail_emails:
        return {"message": "No emails found", "total": 0, "results": []}

    results: list[dict] = []
    for gm in gmail_emails:
        body = gm["body"]
        if not body or len(body.strip()) < 10:
            continue

        _, sender_addr = parseaddr(gm["sender"])

        emotion = detect_emotions(body)
        manipulation = detect_patterns(body)
        links = verify_links(body, sender_addr)
        risk = score_email(emotion, manipulation, links)
        triggers = get_trigger_scores(emotion)

        email_id = str(uuid.uuid4())
        snippet = body[:200] + "..." if len(body) > 200 else body

        db.add(AnalyzedEmail(
            id=email_id,
            user_id=user_email,
            subject=gm["subject"],
            sender=sender_addr,
            risk_score=risk.finalScore,
            risk_tier=risk.tier,
            snippet=snippet,
            body=body,
            analyzed_at=datetime.now(timezone.utc),
        ))

        results.append({
            "id": email_id,
            "gmail_id": gm["gmail_id"],
            "subject": gm["subject"],
            "sender": gm["sender"],
            "date": gm["date"],
            "riskScore": risk.finalScore,
            "riskTier": risk.tier,
            "snippet": snippet,
            "triggers": triggers.model_dump(),
            "techniques": len(manipulation.techniques),
            "explanation": risk.explanation,
        })

    results.sort(key=lambda x: x["riskScore"], reverse=True)

    high = sum(1 for r in results if r["riskTier"] == "High")
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=user_email,
        action=f"Gmail scan: {len(results)} emails analyzed, {high} HIGH risk",
        timestamp=datetime.now(timezone.utc),
    ))
    db.commit()

    return {
        "message": f"Analyzed {len(results)} emails",
        "total": len(results),
        "high_risk": high,
        "medium_risk": sum(1 for r in results if r["riskTier"] == "Medium"),
        "low_risk": sum(1 for r in results if r["riskTier"] == "Low"),
        "results": results,
    }
