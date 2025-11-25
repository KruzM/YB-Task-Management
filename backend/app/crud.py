from sqlalchemy.orm import Session
from . import models
from backend.app.schemas.users import UserCreate
from sqlalchemy.exc import IntegrityError
from .models import Client, Task, TaskAssignment
from .schemas.clients import ClientCreate, ClientUpdate
import json
from datetime import datetime
from backend.app.services.recurrence.evaluator import evaluate_task_for_recurrence
from backend.app.services.recurrence.notifications import send_notification
from backend.app.services.recurrence.generator import create_next_recurring_task

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

# =============================
# CLIENT CRUD OPERATIONS
# =============================

def create_client(db, client_data: ClientCreate):
    new_client = Client(**client_data.dict())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


def get_clients(db):
    return db.query(Client).all()


def get_client_by_id(db, client_id: int):
    return db.query(Client).filter(Client.id == client_id).first()


def update_client(db, client_id: int, upd: ClientUpdate):
    client = get_client_by_id(db, client_id)
    if not client:
        return None

    for field, value in upd.dict(exclude_unset=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db, client_id: int):
    client = get_client_by_id(db, client_id)
    if not client:
        return False

    db.delete(client)
    db.commit()
    return True

# =============================
# AUDIT LOG 
# =============================

# def create_audit(db: Session, payload):
#     obj = AuditLog(
#         actor_id=payload.actor_id,
#         actor_email=payload.actor_email,
#         target_type=payload.target_type,
#         target_id=payload.target_id,
#         action=payload.action,
#         details=json.dumps(payload.details) if payload.details else None,
#         ip_address=payload.ip_address,
#         user_agent=payload.user_agent,
#     )
#     db.add(obj)
#     db.commit()
#     db.refresh(obj)
#     return obj

# def list_audit(db: Session, skip=0, limit=100):
#     return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()


# def get_recurring_master_tasks_due(db: Session, now: datetime):
#     return db.query(Task).filter(Task.is_recurring == True, Task.parent_task_id == None, Task.due_date <= now).all()

# ---------------------
# Task completion helper (crud.py)
# ---------------------


def mark_task_completed(db, task_id: int, actor_id: int | None = None):
    """
    Marks a task as completed.
    If it is recurring AND all subtasks completed, generate the next occurrence.
    """
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None

    # Mark task as completed
    task.status = "completed"
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    # If not a recurring task ? no further action
    if not task.is_recurring:
        return {"task": task, "generated": None}

    # -----------------------------
    # Run recurrence evaluator
    # -----------------------------
    generated = evaluate_task_for_recurrence(
        db=db,
        task_model=models.Task,
        subtask_model=models.Subtask,
        task_instance=task,
        commit=True,
        notification_hook=send_notification
    )

    return {"task": task, "generated": generated}
