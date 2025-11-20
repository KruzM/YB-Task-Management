from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from fastapi import Security, HTTPException, status, Header
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from fastapi.security.api_key import APIKeyHeader

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------
# TOKEN UTILITIES
# -----------------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# -----------------------------
# GET CURRENT USER (single canonical dependency)
# -----------------------------
# This reads the "Authorization" header (case-sensitive as HTTP uses) and supports:
#   Authorization: Bearer <token>
# or
#   Authorization: <token>
def get_current_user(
    authorization: str = Header(default=None, alias="Authorization"),
    db: Session = Security(get_db)
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    # allow "Bearer <token>" or just "<token>"
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload["sub"]
    # the token might contain sub as string; be flexible
    try:
        user_id_int = int(user_id)
    except Exception:
        user_id_int = user_id

    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user