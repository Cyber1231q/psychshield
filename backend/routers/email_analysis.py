"""Email analysis router — runs the detection pipeline on submitted emails.

Endpoints:
    POST /api/analyze-email — Accept email text, run all detectors,
                              return risk score and breakdown.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from detectors.emotion_detector import detect_emotions
from detectors.link_verifier import verify_links, verify_sender
from detectors.manipulation_detector import detect_patterns
from detectors.risk_scorer import get_trigger_scores, score_email
from models.database import get_db
from models.entities import AnalyzedEmail, AuditLog
from models.entities import AnalysisResult as DBAnalysisResult
from models.schemas import AnalysisResult, EmailAnalysisRequest
from routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("psychshield")


def _extract_subject(body: str) -> str:
    """Pull the first meaningful line from the email as a subject."""
    for line in body.strip().split("\n"):
        clean = line.strip()
        if clean and len(clean) > 5:
            return clean[:100]
    return "No subject"


@router.post("/analyze-email", response_model=AnalysisResult)
def analyze_email(
    request: EmailAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    """Run the full detection pipeline on a submitted email.

    Args:
        request: Email body and optional sender address.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        Complete analysis breakdown matching the frontend AnalysisResult shape.
    """
    start_time = time.time()

    body = request.body
    sender = request.sender or ""

    emotion_result = detect_emotions(body)
    manipulation_result = detect_patterns(body)
    link_result = verify_links(body, sender)
    sender_info = verify_sender(sender) if sender else None
    risk_report = score_email(emotion_result, manipulation_result, link_result)
    trigger_scores = get_trigger_scores(emotion_result)

    email_id = str(uuid.uuid4())
    snippet = body[:150] + "..." if len(body) > 150 else body
    now = datetime.now(timezone.utc)

    db_email = AnalyzedEmail(
        id=email_id,
        user_id=current_user.get("sub", ""),
        subject=_extract_subject(body),
        sender=sender or "Unknown",
        risk_score=risk_report.finalScore,
        risk_tier=risk_report.tier,
        snippet=snippet,
        body=body,
        analyzed_at=now,
    )
    db.add(db_email)

    sv_json = json.dumps(sender_info.model_dump(by_alias=True)) if sender_info else "{}"
    db_analysis = DBAnalysisResult(
        id=str(uuid.uuid4()),
        email_id=email_id,
        emotion_score=emotion_result.emotionScore,
        manipulation_score=manipulation_result.patternScore,
        link_score=link_result.linkScore,
        composite_score=risk_report.finalScore / 100,
        tier=risk_report.tier,
        explanation=risk_report.explanation,
        triggers_json=json.dumps(trigger_scores.model_dump()),
        techniques_json=json.dumps(
            [t.model_dump() for t in manipulation_result.techniques]
        ),
        urls_json=json.dumps([u.model_dump() for u in link_result.urls]),
        sender_verification_json=sv_json,
        analyzed_at=now,
    )
    db.add(db_analysis)

    audit = AuditLog(
        id=str(uuid.uuid4()),
        actor=current_user.get("sub", "system"),
        action=(
            f"Email {email_id} classified {risk_report.tier} "
            f"(score {risk_report.finalScore})"
        ),
        timestamp=now,
    )
    db.add(audit)
    db.commit()

    latency_ms = (time.time() - start_time) * 1000
    if latency_ms > 3000:
        logger.warning("Analysis latency %.0fms exceeds 3s target", latency_ms)

    return AnalysisResult(
        id=email_id,
        sender=sender,
        receivedAt=now.isoformat(),
        riskScore=risk_report.finalScore,
        riskTier=risk_report.tier,
        bodyPreview=snippet,
        emotionDetection=emotion_result,
        manipulationPattern=manipulation_result,
        linkVerification=link_result,
        triggers=trigger_scores,
        riskReport=risk_report,
        senderVerification=sender_info,
    )
