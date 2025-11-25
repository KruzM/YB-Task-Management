from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.app.models import AuditLog


def log_audit_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    performed_by: Optional[int] = None,
    details: dict | None = None,
):
    """General audit logging function for any action."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by=performed_by,
        details=details or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def log_task_action(
    db: Session,
    action: str,
    task_id: int,
    performed_by: int,
    details: dict | None = None,
):
    """Persist a simple audit entry for task-related actions."""
    return log_audit_action(
        db=db,
        action=action,
        entity_type="task",
        entity_id=task_id,
        performed_by=performed_by,
        details=details or {},
    )


def log_client_action(
    db: Session,
    action: str,
    client_id: int,
    performed_by: int,
    details: dict | None = None,
):
    """Log client-related actions."""
    return log_audit_action(
        db=db,
        action=action,
        entity_type="client",
        entity_id=client_id,
        performed_by=performed_by,
        details=details or {},
    )


def log_user_action(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    performed_by: Optional[int] = None,
    details: dict | None = None,
):
    """Log user-related actions (login, logout, user creation, etc.)."""
    return log_audit_action(
        db=db,
        action=action,
        entity_type="user",
        entity_id=user_id,
        performed_by=performed_by,
        details=details or {},
    )


def log_permission_action(
    db: Session,
    action: str,
    entity_id: Optional[int] = None,
    performed_by: Optional[int] = None,
    details: dict | None = None,
):
    """Log permission/role-related actions."""
    return log_audit_action(
        db=db,
        action=action,
        entity_type="permission",
        entity_id=entity_id,
        performed_by=performed_by,
        details=details or {},
    )


def log_document_action(
    db: Session,
    action: str,
    document_id: int,
    performed_by: int,
    details: dict | None = None,
):
    """Log document-related actions."""
    return log_audit_action(
        db=db,
        action=action,
        entity_type="document",
        entity_id=document_id,
        performed_by=performed_by,
        details=details or {},
    )


def list_audit_logs(
    db: Session,
    limit: int = 100,
    skip: int = 0,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    performed_by: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[AuditLog]:
    """List audit logs with optional filtering."""
    query = db.query(AuditLog)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if performed_by:
        query = query.filter(AuditLog.performed_by == performed_by)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    return (
        query
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
