from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.users import UserCreate, UserOut, UserUpdate
from backend.app.utils.security import get_current_user, hash_password
from backend.app.auth import require_admin
from backend.app import crud
from backend.app import models

router = APIRouter(prefix="/users", tags=["Users"])


# -------------------------
# CREATE USER (ADMIN ONLY)
# -------------------------
@router.post("/", response_model=UserOut)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(payload.password)
    user = crud.create_user(db, payload, hashed)
    return user


# -------------------------
# LIST USERS (ADMIN ONLY)
# -------------------------
@router.get("/", response_model=List[UserOut])
def list_users_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return crud.list_users(db)


# -------------------------
# GET SELF
# -------------------------
@router.get("/me", response_model=UserOut)
def read_self(current_user=Depends(get_current_user)):
    return current_user


# -------------------------
# UPDATE SELF OR ADMIN UPDATE ANY USER
# -------------------------
@router.patch("/{user_id}", response_model=UserOut)
def update_user_endpoint(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # user can modify themselves or admin can modify anyone
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    updated = crud.update_user(db, user_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return updated