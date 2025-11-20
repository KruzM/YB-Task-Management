# backend/app/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.utils.security import verify_password, create_access_token, decode_access_token, hash_password, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

auth_scheme = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Login using form (username=password per OAuth2 form spec)
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# Optional helper endpoint to create admin from env vars
@router.post("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    import os
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        raise HTTPException(status_code=500, detail="Admin credentials not set in .env")

    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        return {"message": "Admin already exists"}

    hashed_pw = hash_password(admin_password)

    new_admin = User(
        email=admin_email,
        full_name="Admin",
        is_admin=True,
        hashed_password=hashed_pw
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"message": "Admin created", "email": admin_email}