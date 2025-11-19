from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "employee"