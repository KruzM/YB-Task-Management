from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.schemas import Token, UserLogin
from backend.app.utils.security import verify_password, create_access_token, hash_password

from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = create_access_token.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create token
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    import os

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        raise HTTPException(status_code=500, detail="Admin credentials not set in .env")

    if len(admin_password) > 72:
        raise HTTPException(status_code=400, detail="Admin password exceeds bcrypt 72-byte limit")

    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        return {"message": "Admin already exists"}

    hashed_pw = hash_password(admin_password)

    new_admin = User(
        email=admin_email,
        name="Admin",
        role="admin",
        hashed_password=hashed_pw
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"message": "Admin created", "email": admin_email}