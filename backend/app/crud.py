from sqlalchemy.orm import Session, selectinload
from typing import Optional
from . import models
from backend.app.schemas.users import UserCreate
from sqlalchemy.exc import IntegrityError
from .models import (
    Client,
    Task,
    TaskAssignment,
    Contact,
    Account,
    ClientGroup,
    ClientGroupMember,
    ClientContact,
)
from .schemas.clients import (
    ClientCreate,
    ClientUpdate,
    ContactCreate,
    AccountCreate,
    ClientGroupCreate,
)
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


def get_clients(db, search: Optional[str] = None, status: Optional[str] = None, group_name: Optional[str] = None):
    query = db.query(Client)

    if status:
        query = query.filter(Client.status == status)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(like_pattern)) |
            (Client.primary_contact.ilike(like_pattern)) |
            (Client.primary_email.ilike(like_pattern))
        )

    if group_name:
        query = query.join(Client.group_memberships).join(ClientGroupMember.group).filter(ClientGroup.name == group_name)

    clients = query.options(
        selectinload(Client.contacts),
        selectinload(Client.accounts),
        selectinload(Client.group_memberships)
        .selectinload(ClientGroupMember.group)
        .selectinload(ClientGroup.members),
    ).all()
    return clients


def get_client_by_id(db, client_id: int):
    return (
        db.query(Client)
        .options(
            selectinload(Client.contacts),
            selectinload(Client.accounts),
            selectinload(Client.group_memberships)
            .selectinload(ClientGroupMember.group)
            .selectinload(ClientGroup.members),
        )
        .filter(Client.id == client_id)
        .first()
    )


def update_client(db, client_id: int, upd: ClientUpdate):
    client = get_client_by_id(db, client_id)
    if not client:
        return None

    # Check if status is being changed to inactive/left, mark documents for purge
    upd_dict = upd.dict(exclude_unset=True)
    if 'status' in upd_dict:
        new_status = upd_dict.get('status', '').lower() if upd_dict.get('status') else ''
        old_status = (client.status or '').lower()
        if new_status in ('inactive', 'left', 'closed') and old_status not in ('inactive', 'left', 'closed'):
            from backend.app.crud_utils.documents import mark_client_left
            mark_client_left(db, client_id)

    for field, value in upd_dict.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db, client_id: int):
    client = get_client_by_id(db, client_id)
    if not client:
        return False

    # Mark documents for purge before deleting client
    from backend.app.crud_utils.documents import mark_client_left
    mark_client_left(db, client_id)

    db.delete(client)
    db.commit()
    return True


# =============================
# CONTACTS
# =============================

def create_contact(db: Session, payload: ContactCreate):
    contact = Contact(**payload.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def list_contacts(db: Session, search: Optional[str] = None):
    query = db.query(Contact)
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            (Contact.name.ilike(like_pattern)) |
            (Contact.email.ilike(like_pattern)) |
            (Contact.phone.ilike(like_pattern))
        )
    return query.all()


def attach_contact_to_client(db: Session, client_id: int, contact_id: int, relationship_type: Optional[str] = None):
    existing = (
        db.query(ClientContact)
        .filter(ClientContact.client_id == client_id, ClientContact.contact_id == contact_id)
        .first()
    )
    if existing:
        return existing

    link = ClientContact(
        client_id=client_id,
        contact_id=contact_id,
        relationship_type=relationship_type,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def remove_contact_from_client(db: Session, client_id: int, contact_id: int):
    link = (
        db.query(ClientContact)
        .filter(ClientContact.client_id == client_id, ClientContact.contact_id == contact_id)
        .first()
    )
    if link:
        db.delete(link)
        db.commit()
    return True


# =============================
# ACCOUNTS
# =============================

def create_account(db: Session, payload: AccountCreate, client_id: Optional[int] = None):
    data = payload.dict()
    if client_id:
        data["client_id"] = client_id
    account = Account(**data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts_for_client(db: Session, client_id: int):
    return db.query(Account).filter(Account.client_id == client_id).all()


# =============================
# CLIENT GROUPS
# =============================

def create_client_group(db: Session, payload: ClientGroupCreate):
    group = ClientGroup(**payload.dict())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_client_groups(db: Session):
    return db.query(ClientGroup).all()


def add_client_to_group(db: Session, client_id: int, group_id: int, role: Optional[str] = None):
    existing = (
        db.query(ClientGroupMember)
        .filter(ClientGroupMember.client_id == client_id, ClientGroupMember.group_id == group_id)
        .first()
    )
    if existing:
        return existing

    membership = ClientGroupMember(client_id=client_id, group_id=group_id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership

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
