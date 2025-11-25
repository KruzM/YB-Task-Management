from sqlalchemy.orm import Session

from backend.app.models import AuditLog


def log_task_action(
    db: Session,
    action: str,
    task_id: int,
    performed_by: int,
    details: dict | None = None,
):
    """Persist a simple audit entry for task-related actions."""

    entry = AuditLog(
        action=action,
        entity_type="task",
        entity_id=task_id,
        performed_by=performed_by,
        details=details or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(db: Session, limit: int = 100, skip: int = 0):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
