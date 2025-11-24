from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.crud_utils.audit import list_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/")
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return list_audit_logs(db, limit=limit, skip=skip)