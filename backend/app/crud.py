from sqlalchemy.orm import Session
from . import models, schemas
from backend.app.schemas.users import UserCreate, User

# Get a user by email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# Create a new user (used for admin creation too)
def create_user(db: Session, user: UserCreate, hashed_password: str):
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=user.is_admin if hasattr(user, "is_admin") else False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user