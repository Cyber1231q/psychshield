"""Email analysis router — runs the detection pipeline on submitted emails.

Endpoints:
    POST /api/analyze-email  — Accept one email, run all detectors,
                               return risk score and breakdown.
    POST /api/analyze-emails — Accept a document containing multiple emails,
                               split them server-side, and analyze each as
                               a separate entity (separate sender, separate
                               body, separate stored result).
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from email import message_from_string
from email.utils import parseaddr

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from detectors.emotion_detector import detect_emotions
from detectors.link_verifier import verify_links, verify_sender
from detectors.manipulation_detector import detect_patterns
from detectors.risk_scorer import get_trigger_scores, score_email
from models.database import get_db
from models.entities import AnalyzedEmail, AuditLog
from models.entities import AnalysisResult as DBAnalysisResult
from models.schemas import (
    AnalysisResult,
    BatchEmailAnalysisRequest,
    BatchEmailAnalysisResult,
    EmailAnalysisRequest,
)
from routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("psychshield")

MAX_BATCH_EMAILS = 50


def _extract_subject(body: str) -> str:
    """Pull the first meaningful line from the email as a subject."""
    for line in body.strip().split("\n"):
        clean = line.strip()
        if clean and len(clean) > 5:
            return clean[:100]
    return "No subject"


def _analyze_and_persist(
    body: str, sender: str, current_user: dict, db: Session
) -> AnalysisResult:
    """Run the four-stage pipeline on one email and stage its DB rows.

    Shared by /analyze-email and /analyze-emails so a scoring or
    persistence change only ever needs to be made in one place. Does not
    commit — callers commit once after all emails in a request are staged.
    """
    emotion_result = detect_emotions(body)
    manipulation_result = detect_patterns(body)
    link_result = verify_links(body, sender)
    sender_info = verify_sender(sender) if sender else None
    risk_report = score_email(
        emotion_result,
        manipulation_result,
        link_result,
        sender=sender_info,
    )
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

    result = _analyze_and_persist(request.body, request.sender or "", current_user, db)
    db.commit()

    latency_ms = (time.time() - start_time) * 1000
    if latency_ms > 3000:
        logger.warning("Analysis latency %.0fms exceeds 3s target", latency_ms)

    return result


# ── Multi-email document splitting (server-side) ────────────────────────────
# Mirrors splitEmails()/extractSender() in EmailAnalysis.jsx so "paste a
# document with several emails in it" behaves the same way regardless of
# whether it comes through the browser's paste/upload flow or straight
# through the API from any other client (curl, a script, a future mobile
# app...). That splitting previously existed ONLY client-side — a direct
# POST /analyze-email call always got treated as exactly one email with
# sender="Unknown".

_SEPARATOR_RE = re.compile(r"\n-{3,}\n|\n={3,}\n|\n\*{3,}\n")
_FROM_LINE_RE = re.compile(r"^From:\s*.+@", re.IGNORECASE)
_MARKER_RE = re.compile(r"^(email\s*#?\s*\d+|sample\s*#?\s*\d+|\d+[.)]\s)", re.IGNORECASE)


def _split_by(pattern: "re.Pattern[str]", text: str, min_chunk_len: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        if pattern.match(line) and len(current.strip()) > min_chunk_len:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if len(current.strip()) > 10:
        chunks.append(current.strip())
    return chunks


def _split_document(text: str) -> list[str]:
    """Split one pasted/uploaded document into separate email chunks.

    Tries, in order: explicit separator lines, repeated "From:" header
    lines, then numbered/lettered markers ("Email #2", "3)"). Falls back
    to treating the whole document as a single email.
    """
    chunks = [c.strip() for c in _SEPARATOR_RE.split(text) if len(c.strip()) > 10]
    if len(chunks) > 1:
        return chunks

    chunks = _split_by(_FROM_LINE_RE, text, min_chunk_len=30)
    if len(chunks) > 1:
        return chunks

    chunks = _split_by(_MARKER_RE, text, min_chunk_len=20)
    if len(chunks) > 1:
        return chunks

    return [text.strip()]


def _parse_chunk(chunk: str) -> tuple[str, str]:
    """Parse one chunk's headers with Python's real RFC-822 email parser.

    Returns (body, sender_address). Falls back to (whole chunk, "") when
    the chunk has no "From:"-style header block the parser recognizes —
    common for a plain paste with no header lines at all.
    """
    msg = message_from_string(chunk)
    from_header = msg.get("From")
    if from_header:
        _, sender_addr = parseaddr(from_header)
        payload = msg.get_payload()
        if isinstance(payload, str) and payload.strip():
            return payload.strip(), sender_addr
    return chunk, ""


@router.post("/analyze-emails", response_model=BatchEmailAnalysisResult)
def analyze_emails(
    request: BatchEmailAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchEmailAnalysisResult:
    """Split a document into individual emails and analyze each separately.

    Args:
        request: One document that may contain several emails concatenated
            together (e.g. exported from an inbox, or several samples
            pasted at once).
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        One AnalysisResult per detected email, each persisted as its own
        AnalyzedEmail/AnalysisResult/AuditLog row — same as if each had
        been submitted individually to /analyze-email.
    """
    start_time = time.time()
    chunks = _split_document(request.document)[:MAX_BATCH_EMAILS]

    results: list[AnalysisResult] = []
    for chunk in chunks:
        body, sender = _parse_chunk(chunk)
        results.append(
            _analyze_and_persist(body[:50000], sender[:254], current_user, db)
        )
    db.commit()

    latency_ms = (time.time() - start_time) * 1000
    if latency_ms > 3000:
        logger.warning(
            "Batch analysis latency %.0fms for %d emails", latency_ms, len(chunks)
        )

    return BatchEmailAnalysisResult(count=len(results), results=results)
