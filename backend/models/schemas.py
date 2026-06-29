"""Pydantic schemas for API request/response validation.

Defines all request bodies and response models to match the shapes
expected by the frontend (see psychshield-v2/src/lib/mockData.js).
"""

import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_PASSWORD_MIN_LENGTH = 8
_PASSWORD_RULES = [
    (r"[A-Z]", "at least one uppercase letter"),
    (r"[a-z]", "at least one lowercase letter"),
    (r"\d", "at least one digit"),
    (r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\`~]", "at least one special character"),
]


# ── Request Schemas ──────────────────────────────────────────────

_EMAIL_REGEX = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"


class LoginRequest(BaseModel):
    """POST /api/auth/login request body."""

    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        """Reject malformed email addresses."""
        if not re.match(_EMAIL_REGEX, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class RegisterRequest(BaseModel):
    """POST /api/auth/register request body."""

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        """Reject malformed email addresses."""
        if not re.match(_EMAIL_REGEX, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Enforce complex password policy."""
        errors: list[str] = []
        if len(v) < _PASSWORD_MIN_LENGTH:
            errors.append(f"at least {_PASSWORD_MIN_LENGTH} characters")
        for pattern, message in _PASSWORD_RULES:
            if not re.search(pattern, v):
                errors.append(message)
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v


class GoogleAuthRequest(BaseModel):
    """POST /api/auth/google request body."""

    credential: str = Field(max_length=4096)


class EmailAnalysisRequest(BaseModel):
    """POST /api/analyze-email request body."""

    body: str = Field(min_length=1, max_length=50000)
    sender: Optional[str] = Field(default=None, max_length=254)


# ── Response Schemas ─────────────────────────────────────────────

class EmotionCategoryScore(BaseModel):
    """A single emotion category and its confidence score."""

    category: str
    score: float


class EmotionDetectionResult(BaseModel):
    """Output from the emotion detector module."""

    model: str
    categoryScores: List[EmotionCategoryScore]
    emotionScore: float
    summary: str
    model_config = ConfigDict(populate_by_name=True)


class ManipulationTechnique(BaseModel):
    """A detected manipulation technique with supporting evidence."""

    name: str
    evidence: str


class ManipulationResult(BaseModel):
    """Output from the manipulation detector module."""

    model: str
    patternScore: float
    techniques: List[ManipulationTechnique]
    model_config = ConfigDict(populate_by_name=True)


class URLFlag(BaseModel):
    """A flagged URL with risk indicators."""

    url: str
    flags: List[str]
    riskLevel: str
    model_config = ConfigDict(populate_by_name=True)


class LinkVerificationResult(BaseModel):
    """Output from the link verifier module."""

    model: str
    linkScore: float
    urls: List[URLFlag]
    model_config = ConfigDict(populate_by_name=True)


class SenderVerification(BaseModel):
    """Sender identity and authentication check results."""

    from_: str = Field(alias="from")
    displayName: str
    replyTo: Optional[str] = None
    domain: str
    typosquatted: bool
    spf: str
    dkim: str
    dmarc: str
    domainAgeDays: Optional[int] = None
    model_config = ConfigDict(populate_by_name=True)


class TriggerScores(BaseModel):
    """Per-trigger confidence scores for the radar/trigger map."""

    urgency: float
    fear: float
    authority: float
    trust: float
    pity: float


class RiskReport(BaseModel):
    """Final risk assessment combining all detector outputs."""

    weightedFormula: str
    finalScore: int
    tier: str
    explanation: str
    model_config = ConfigDict(populate_by_name=True)


class AnalysisResult(BaseModel):
    """Full analysis result for a single email — matches mockAnalysisResult."""

    id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    receivedAt: Optional[str] = None
    riskScore: int
    riskTier: str
    bodyPreview: str
    emotionDetection: EmotionDetectionResult
    manipulationPattern: ManipulationResult
    linkVerification: LinkVerificationResult
    triggers: TriggerScores
    riskReport: RiskReport
    senderVerification: Optional[SenderVerification] = None
    model_config = ConfigDict(populate_by_name=True)


class EmailListItem(BaseModel):
    """Summary item for the emails list — matches mockEmails entries."""

    id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    receivedAt: Optional[str] = None
    riskScore: int
    riskTier: str
    snippet: str
    model_config = ConfigDict(populate_by_name=True)


class LoginResponse(BaseModel):
    """POST /api/auth/login response."""

    token: str
    user: dict


# ── Analytics Schemas (matches mockAnalytics) ────────────────────

class TrendPoint(BaseModel):
    """A single data point in the detection rate trend chart."""

    date: str
    high: int
    medium: int
    low: int


class TopTrigger(BaseModel):
    """A trigger type with its occurrence count."""

    trigger: str
    count: int


class AnalyticsResponse(BaseModel):
    """GET /api/analytics response — matches mockAnalytics."""

    totalAnalyzed: int
    highRisk: int
    mediumRisk: int
    lowRisk: int
    detectionRateTrend: List[TrendPoint]
    topTriggers: List[TopTrigger]
    model_config = ConfigDict(populate_by_name=True)


# ── Audit Log Schema (matches mockAuditLog) ─────────────────────

class AuditLogEntry(BaseModel):
    """A single audit log record — matches mockAuditLog entries."""

    id: str
    timestamp: str
    actor: str
    action: str


# ── User Schema (matches mockUsers) ─────────────────────────────

class UserOut(BaseModel):
    """Public user representation — matches mockUsers entries."""

    id: str
    name: str
    email: str
    role: str
    lastLogin: Optional[str] = None
    status: str
    model_config = ConfigDict(populate_by_name=True)


# ── Model Metrics Schema (matches mockModelMetrics) ─────────────

class ModelMetrics(BaseModel):
    """ML model performance metrics for the admin dashboard."""

    accuracy: float
    highRecall: float
    precision: float
    f1Score: float
    avgLatencyMs: int
    lastEvaluated: str
    model_config = ConfigDict(populate_by_name=True)


# ── Password Reset Schemas ─────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    """POST /api/auth/forgot-password request body."""

    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        """Reject malformed email addresses."""
        if not re.match(_EMAIL_REGEX, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class ResetPasswordRequest(BaseModel):
    """POST /api/auth/reset-password request body."""

    token: str = Field(max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class ValidateTokenRequest(BaseModel):
    """POST /api/auth/validate-reset-token request body."""

    token: str = Field(max_length=256)


class MessageResponse(BaseModel):
    """Generic single-message response."""

    message: str
