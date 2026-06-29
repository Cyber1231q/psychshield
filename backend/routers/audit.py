"""Audit log router — tracks all user and system actions.

Endpoints:
    GET /api/audit-log — Return audit log entries, newest first.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db
from models.entities import AuditLog
from models.schemas import AuditLogEntry
from routers.auth import require_admin

router = APIRouter()


@router.get("/audit-log", response_model=List[AuditLogEntry])
def get_audit_log(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AuditLogEntry]:
    """Return all audit log entries, newest first.

    Args:
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        List of audit log entries.
    """
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return [
        AuditLogEntry(
            id=row.id,
            timestamp=row.timestamp.isoformat() if row.timestamp else "",
            actor=row.actor,
            action=row.action,
        )
        for row in rows
    ]
