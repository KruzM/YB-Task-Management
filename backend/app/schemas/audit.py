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

class AuditResponse(AuditBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True