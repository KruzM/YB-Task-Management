from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class AuditBase(BaseModel):
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    target_type: str
    target_id: Optional[int] = None
    action: str
    details: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditCreate(AuditBase):
    pass

class AuditResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    performed_by: Optional[int] = None
    timestamp: datetime
    details: Optional[dict] = None
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None

    class Config:
        orm_mode = True