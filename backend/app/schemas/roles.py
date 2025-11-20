from pydantic import BaseModel
from typing import List, Optional

class PermissionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    permissions: List[int] = []

class RoleOut(RoleBase):
    id: int
    name: str
    permissions: List[PermissionOut] = []

    class Config:
        orm_mode = True


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    add_permissions: Optional[List[int]] = None
    remove_permissions: Optional[List[int]] = None

