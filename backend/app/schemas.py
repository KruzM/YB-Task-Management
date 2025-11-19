from pydantic import BaseModel
from typing import Optional


# -----------------------
# USER SCHEMAS
# -----------------------

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


# -----------------------
# AUTH SCHEMAS
# -----------------------

class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str] = None