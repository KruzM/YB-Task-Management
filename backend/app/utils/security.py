# backend/app/utils/security.py
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import models

SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
INACTIVITY_TIMEOUT_MINUTES = int(os.getenv("INACTIVITY_TIMEOUT_MINUTES", "60"))  # 1 hour default

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from e

def hash_token(token: str) -> str:
    """Create a hash of the token for session tracking"""
    return hashlib.sha256(token.encode()).hexdigest()


def create_or_update_session(db: Session, user_id: int, token: str, expires_delta: timedelta) -> models.UserSession:
    """Create or update a user session"""
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + expires_delta
    
    # Check if session exists
    session = db.query(models.UserSession).filter(
        models.UserSession.user_id == user_id,
        models.UserSession.token_hash == token_hash,
    ).first()
    
    if session:
        # Update last activity and expiration
        session.last_activity = datetime.utcnow()
        session.expires_at = expires_at
    else:
        # Create new session
        session = models.UserSession(
            user_id=user_id,
            token_hash=token_hash,
            last_activity=datetime.utcnow(),
            expires_at=expires_at,
        )
        db.add(session)
    
    db.commit()
    db.refresh(session)
    return session


def check_session_activity(db: Session, user_id: int, token: str) -> bool:
    """
    Check if session is still active (within inactivity timeout).
    Updates last_activity if valid.
    Returns True if valid, False if expired.
    """
    token_hash = hash_token(token)
    inactivity_timeout = timedelta(minutes=INACTIVITY_TIMEOUT_MINUTES)
    
    session = db.query(models.UserSession).filter(
        models.UserSession.user_id == user_id,
        models.UserSession.token_hash == token_hash,
    ).first()
    
    if not session:
        return False
    
    # Check if session expired
    if datetime.utcnow() > session.expires_at:
        # Delete expired session
        db.delete(session)
        db.commit()
        return False
    
    # Check inactivity timeout
    time_since_activity = datetime.utcnow() - session.last_activity
    if time_since_activity > inactivity_timeout:
        # Session expired due to inactivity
        db.delete(session)
        db.commit()
        return False
    
    # Update last activity
    session.last_activity = datetime.utcnow()
    db.commit()
    return True


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user_id = int(sub)
    except:
        user = db.query(models.User).filter(models.User.email == str(sub)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    # Check session activity (1-hour inactivity timeout)
    if not check_session_activity(db, user_id, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired due to inactivity. Please log in again.",
        )
    
    return user
