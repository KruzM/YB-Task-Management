from pydantic import BaseModel
from typing import List, Optional

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionOut(PermissionBase):
    id: int
    class Config:
        orm_mode = True


class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    permissions: List[int] = []  # permission IDs

class RoleOut(RoleBase):
    id: int
    permissions: List[PermissionOut]
    class Config:
        orm_mode = True
