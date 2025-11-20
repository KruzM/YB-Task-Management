from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    email: str
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: str = "user"


class User(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str
    is_active: bool = True

    class Config:
        orm_mode = True