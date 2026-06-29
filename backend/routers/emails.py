"""Emails router — CRUD operations for analyzed emails.

Endpoints:
    GET /api/emails      — List all analyzed emails for the current user.
    GET /api/emails/{id} — Retrieve a single analyzed email by ID.
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.entities import AnalyzedEmail
from models.entities import AnalysisResult as DBAnalysisResult
from models.schemas import (
    AnalysisResult,
    EmailListItem,
    EmotionDetectionResult,
    LinkVerificationResult,
    ManipulationResult,
    ManipulationTechnique,
    RiskReport,
    SenderVerification,
    TriggerScores,
    URLFlag,
)
from routers.auth import get_current_user

router = APIRouter()


@router.get("/emails", response_model=List[EmailListItem])
def list_emails(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EmailListItem]:
    """Return all analyzed emails, newest first.

    Args:
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        List of email summary items.
    """
    rows = (
        db.query(AnalyzedEmail)
        .filter(AnalyzedEmail.user_id == current_user["sub"])
        .order_by(AnalyzedEmail.analyzed_at.desc())
        .all()
    )
    items: list[EmailListItem] = []
    for row in rows:
        subject = row.subject
        if not subject:
            subject = row.body[:80] if row.body else "No subject"
        items.append(EmailListItem(
            id=row.id,
            subject=subject,
            sender=row.sender or "Unknown sender",
            receivedAt=row.analyzed_at.isoformat() if row.analyzed_at else None,
            riskScore=row.risk_score,
            riskTier=row.risk_tier,
            snippet=row.body[:200] if row.body else "",
        ))
    return items


@router.get("/emails/{email_id}", response_model=AnalysisResult)
def get_email(
    email_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    """Return the full analysis for a single email.

    Args:
        email_id: UUID of the analyzed email.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        Complete analysis breakdown.
    """
    email_row = db.query(AnalyzedEmail).filter(
        AnalyzedEmail.id == email_id,
        AnalyzedEmail.user_id == current_user["sub"],
    ).first()
    if not email_row:
        raise HTTPException(status_code=404, detail="Email not found")

    analysis = (
        db.query(DBAnalysisResult)
        .filter(DBAnalysisResult.email_id == email_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    triggers_data = json.loads(analysis.triggers_json or "{}")
    techniques_data = json.loads(analysis.techniques_json or "[]")
    urls_data = json.loads(analysis.urls_json or "[]")
    sv_data = json.loads(analysis.sender_verification_json or "{}")

    trigger_scores = TriggerScores(**triggers_data) if triggers_data else TriggerScores(
        urgency=0, fear=0, authority=0, trust=0, pity=0
    )

    techniques = [ManipulationTechnique(**t) for t in techniques_data]
    urls = [URLFlag(**u) for u in urls_data]

    sender_verification = None
    if sv_data and sv_data.get("from"):
        sender_verification = SenderVerification(**sv_data)

    return AnalysisResult(
        id=email_row.id,
        subject=email_row.subject,
        sender=email_row.sender,
        receivedAt=email_row.analyzed_at.isoformat() if email_row.analyzed_at else None,
        riskScore=email_row.risk_score,
        riskTier=email_row.risk_tier,
        bodyPreview=email_row.snippet,
        emotionDetection=EmotionDetectionResult(
            model="stored",
            categoryScores=[],
            emotionScore=analysis.emotion_score,
            summary=analysis.explanation,
        ),
        manipulationPattern=ManipulationResult(
            model="stored",
            patternScore=analysis.manipulation_score,
            techniques=techniques,
        ),
        linkVerification=LinkVerificationResult(
            model="stored",
            linkScore=analysis.link_score,
            urls=urls,
        ),
        triggers=trigger_scores,
        riskReport=RiskReport(
            weightedFormula="Emotion*0.40 + Pattern*0.35 + Link*0.25",
            finalScore=email_row.risk_score,
            tier=email_row.risk_tier,
            explanation=analysis.explanation,
        ),
        senderVerification=sender_verification,
    )
