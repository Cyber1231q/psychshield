"""SQLAlchemy ORM entity definitions.

Defines database tables: User, AnalyzedEmail, AnalysisResult, AuditLog
and their relationships.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from models.database import Base


class User(Base):
    """Application user — admin or analyst."""

    __tablename__ = "users"

    id: str = Column(String, primary_key=True)
    email: str = Column(String, unique=True, nullable=False, index=True)
    password_hash: str = Column(String, nullable=False)
    role: str = Column(String, default="analyst")
    name: str = Column(String, nullable=False)
    last_login: datetime | None = Column(DateTime, nullable=True)
    status: str = Column(String, default="active")
    created_at: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class AnalyzedEmail(Base):
    """An email that has been submitted for analysis."""

    __tablename__ = "emails"

    id: str = Column(String, primary_key=True)
    user_id: str = Column(String, nullable=False, index=True)
    subject: str | None = Column(String, nullable=True)
    sender: str | None = Column(String, nullable=True)
    received_at: str | None = Column(String, nullable=True)
    risk_score: int = Column(Integer, default=0)
    risk_tier: str = Column(String, default="Low")
    snippet: str = Column(Text, default="")
    body: str = Column(Text, default="")
    analyzed_at: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    analysis = relationship("AnalysisResult", back_populates="email", uselist=False)


class AnalysisResult(Base):
    """Detailed detection results linked to an analyzed email."""

    __tablename__ = "analysis_results"

    id: str = Column(String, primary_key=True)
    email_id: str = Column(String, ForeignKey("emails.id"), nullable=False)
    emotion_score: float = Column(Float, default=0.0)
    manipulation_score: float = Column(Float, default=0.0)
    link_score: float = Column(Float, default=0.0)
    composite_score: float = Column(Float, default=0.0)
    tier: str = Column(String, default="Low")
    explanation: str = Column(Text, default="")
    triggers_json: str = Column(Text, default="{}")
    techniques_json: str = Column(Text, default="[]")
    urls_json: str = Column(Text, default="[]")
    sender_verification_json: str = Column(Text, default="{}")
    analyzed_at: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    email = relationship("AnalyzedEmail", back_populates="analysis")


class AuditLog(Base):
    """Immutable record of user and system actions."""

    __tablename__ = "audit_log"

    id: str = Column(String, primary_key=True)
    timestamp: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    actor: str = Column(String, nullable=False)
    action: str = Column(Text, nullable=False)


class GmailToken(Base):
    """Encrypted Gmail OAuth credentials — one row per user."""

    __tablename__ = "gmail_tokens"

    id: str = Column(String, primary_key=True)
    user_email: str = Column(String, unique=True, nullable=False, index=True)
    encrypted_blob: str = Column(Text, nullable=False)
    connected_at: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_used: datetime | None = Column(DateTime, nullable=True)


class PasswordResetToken(Base):
    """Time-limited, single-use token for password resets."""

    __tablename__ = "password_reset_tokens"

    id: str = Column(String, primary_key=True)
    user_email: str = Column(String, nullable=False, index=True)
    token_hash: str = Column(String, nullable=False)
    expires_at: datetime = Column(DateTime, nullable=False)
    used: bool = Column(Boolean, default=False)
    created_at: datetime = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ip_address: str | None = Column(String, nullable=True)
