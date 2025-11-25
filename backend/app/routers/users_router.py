from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from backend.app.models import Role, Permission, RolePermission, User
from backend.app.database import get_db
from backend.app.schemas.users import UserCreate, UserOut, UserUpdate
from backend.app.utils.security import get_current_user, hash_password
from backend.app import crud
from backend.app import models
from backend.app.utils.permissions import require_permission
from backend.app.crud_utils.audit import log_user_action
router = APIRouter(prefix="/users", tags=["Users"])


# -------------------------
# CREATE USER (ADMIN ONLY)
# -------------------------
@router.post("/", response_model=UserOut)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles")),
):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(payload.password)
    user = crud.create_user(db, payload, hashed)
    
    # Log user creation
    log_user_action(
        db=db,
        action="user_created",
        user_id=user.id,
        performed_by=current_user.id,
        details={
            "created_user_email": user.email,
            "created_user_full_name": user.full_name,
            "role_id": user.role_id,
        },
    )
    
    return user


# -------------------------
# LIST USERS (ADMIN ONLY)
# -------------------------
@router.get("/", response_model=List[UserOut])
def list_users_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_roles")),
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

    updated = crud.update_user(db, user_id, updates, performed_by=current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return updated
