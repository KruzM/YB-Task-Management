# backend/app/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import os

from backend.app.database import get_db
from backend.app import models
from backend.app.utils.security import (
    verify_password,
    create_access_token,
    hash_password,
    get_current_user,
    create_or_update_session,
)
from .schemas.users import UserCreate  # ? ONLY NEED UserCreate
from .crud import create_user, get_user_by_email
from .crud_utils.audit import log_user_action

router = APIRouter(prefix="/auth", tags=["Auth"])

def create_access_token_for_user(user):
    return create_access_token({"sub": str(user.id)})

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username
    password = form_data.password

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        # Log failed login attempt
        if user:
            log_user_action(
                db=db,
                action="login_failed",
                user_id=user.id,
                performed_by=user.id,
                details={"email": email, "reason": "Invalid password"},
            )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token_for_user(user)
    
    # Create or update session for inactivity tracking
    expires_delta = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")))
    create_or_update_session(db, user.id, access_token, expires_delta)

    # Log successful login
    log_user_action(
        db=db,
        action="login",
        user_id=user.id,
        performed_by=user.id,
        details={"email": email},
    )

    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax")
    cookie_max_age = int(os.getenv("COOKIE_MAX_AGE", 7 * 24 * 3600))

    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=cookie_max_age,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": getattr(user, "full_name", None),
            "role_id": getattr(user, "role_id", None),
        },
    }

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Delete session from database
    token = request.cookies.get("token")
    if not token:
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    
    if token and current_user:
        from backend.app.utils.security import hash_token
        token_hash = hash_token(token)
        session = db.query(models.UserSession).filter(
            models.UserSession.user_id == current_user.id,
            models.UserSession.token_hash == token_hash,
        ).first()
        if session:
            db.delete(session)
            db.commit()
        
        # Log logout
        log_user_action(
            db=db,
            action="logout",
            user_id=current_user.id,
            performed_by=current_user.id,
            details={"email": current_user.email},
        )
    
    response.delete_cookie("token", path="/")
    return {"message": "Logged out"}

@router.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # Only admins can register new users
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create new users.")

    # Ensure email not taken
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_pw = hash_password(user.password)
    new_user = create_user(db, user, hashed_pw)

    # Log user creation
    log_user_action(
        db=db,
        action="user_created",
        user_id=new_user.id,
        performed_by=current_user.id,
        details={
            "created_user_email": new_user.email,
            "created_user_full_name": new_user.full_name,
            "role_id": new_user.role_id,
        },
    )

    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role_id": new_user.role_id,
        },
    }