from sqlalchemy.orm import Session
from backend.app.models import AuditLog

def list_audit_logs(db: Session, limit: int = 100, skip: int = 0):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )