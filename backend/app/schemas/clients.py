from pydantic import BaseModel
from typing import Optional, List

# -------------------------
# Base Shared Fields
# -------------------------
class ClientBase(BaseModel):
    name: str
    primary_contact: Optional[str] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None
    cpa: Optional[str] = None
    manager: Optional[str] = None
    billing_frequency: Optional[str] = None
    autopay: Optional[bool] = False
    notes: Optional[str] = None


# -------------------------
# Create Client Schema
# -------------------------
class ClientCreate(ClientBase):
    pass


# -------------------------
# Update Schema
# -------------------------
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    primary_contact: Optional[str] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None
    cpa: Optional[str] = None
    manager: Optional[str] = None
    billing_frequency: Optional[str] = None
    autopay: Optional[bool] = None
    notes: Optional[str] = None


# -------------------------
# Response Schema
# -------------------------

class ClientResponse(ClientBase):
    id: int
    tasks: List = []  # prevent ResponseValidationError
    # If you have client-specific assignments, include them:
    assignments: List = []

    class Config:
        orm_mode = True