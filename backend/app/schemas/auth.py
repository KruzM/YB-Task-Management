from pydantic import BaseModel
from typing import Optional


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str] = None

class UserRole(BaseModel):
    id: int
    name: str
    permissions: list

class UserInfo(BaseModel):
    id: int
    email: str
    role: Optional[UserRole]

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserInfo