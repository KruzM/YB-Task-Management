from sqlalchemy.orm import Session
from . import models, schemas
from backend.app.schemas.users import UserCreate
from sqlalchemy.exc import IntegrityError

# Get a user by email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def list_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

# Create a new user (used for admin creation too)

def create_user(db: Session, user, hashed_password: str):
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active if hasattr(user, "is_active") else True,
        is_admin=user.is_admin if hasattr(user, "is_admin") else False,
        role_id=getattr(user, "role_id", None)
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_user)
    # Auto-assign admin role if is_admin True
    if db_user.is_admin and (not db_user.role_id):
        admin_role = db.query(models.Role).filter(models.Role.name == "Admin").first()
        if admin_role:
            db_user.role_id = admin_role.id
            db.commit()
            db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, updates):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    if updates.full_name is not None:
        db_user.full_name = updates.full_name
    if updates.password:
        from backend.app.utils.security import hash_password
        db_user.hashed_password = hash_password(updates.password)
    if updates.is_active is not None:
        db_user.is_active = updates.is_active
    if updates.role_id is not None:
        db_user.role_id = updates.role_id
    db.commit()
    db.refresh(db_user)
    return db_user

def set_user_role(db: Session, user_id: int, role_id: int):
    u = get_user_by_id(db, user_id)
    if not u:
        return None
    u.role_id = role_id
    db.commit()
    db.refresh(u)
    return u

def deactivate_user(db: Session, user_id: int):
    u = get_user_by_id(db, user_id)
    if not u:
        return None
    u.is_active = False
    db.commit()
    db.refresh(u)
    return u

def activate_user(db: Session, user_id: int):
    u = get_user_by_id(db, user_id)
    if not u:
        return None
    u.is_active = True
    db.commit()
    db.refresh(u)
    return u