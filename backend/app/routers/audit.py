from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime

from backend.app.database import get_db
from backend.app.utils.security import get_current_user
from backend.app.crud_utils.audit import list_audit_logs
from backend.app.schemas.audit import AuditResponse
from backend.app.models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/", response_model=List[AuditResponse])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (task, client, user, etc.)"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    performed_by: Optional[int] = Query(None, description="Filter by user ID who performed the action"),
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs until this date"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get audit logs with optional filtering. Only admins can view all logs."""
    # Non-admins can only see their own audit logs
    if not current_user.is_admin:
        performed_by = current_user.id
    
    logs = list_audit_logs(
        db=db,
        limit=limit,
        skip=skip,
        entity_type=entity_type,
        action=action,
        performed_by=performed_by,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Load user relationships and format response
    result = []
    for log in logs:
        user_email = None
        user_full_name = None
        if log.performed_by:
            user = db.query(User).filter(User.id == log.performed_by).first()
            if user:
                user_email = user.email
                user_full_name = user.full_name
        
        result.append(AuditResponse(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            performed_by=log.performed_by,
            timestamp=log.timestamp,
            details=log.details,
            user_email=user_email,
            user_full_name=user_full_name,
        ))
    
    return result