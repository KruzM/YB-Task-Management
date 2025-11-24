# ---------------------
# SQLAlchemy models for YB Task Management
# ---------------------
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text, Float, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

# ---------------------
# Role & Permission Models
# ---------------------
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    permissions = relationship("RolePermission", back_populates="role")
    users = relationship("User", back_populates="role")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uix_role_permission"),
    )


# ---------------------
# Task Status Enum
# ---------------------
class TaskStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    completed = "completed"


# ---------------------
# User Model
# ---------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    client_assignments = relationship("ClientAssignment", back_populates="user")
    task_assignments = relationship("TaskAssignment", back_populates="user")
    role_id = Column(Integer, ForeignKey("roles.id"), default=1)
    role = relationship("Role", back_populates="users")


# ---------------------
# Client Model
# ---------------------
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String, nullable=False)
    primary_contact = Column(String, nullable=True)
    primary_email = Column(String, nullable=True)
    primary_phone = Column(String, nullable=True)

    # Internal assigned staff
    cpa = Column(String, nullable=True)
    manager = Column(String, nullable=True)

    # Billing & frequency
    billing_frequency = Column(String, nullable=True)  # monthly / quarterly / annually
    autopay = Column(Boolean, default=False)

    # Notes or future use
    notes = Column(String, nullable=True)

    # Relationship to tasks (one-to-many)
    tasks = relationship("Task", back_populates="client", cascade="all, delete")
    assignments = relationship("ClientAssignment", back_populates="client", cascade="all, delete")


class ClientAssignment(Base):
    __tablename__ = "client_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))

    user = relationship("User", back_populates="client_assignments")
    client = relationship("Client", back_populates="assignments")


# ---------------------
# Task Model
# ---------------------
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    # ---------------------
    # Basic task fields
    # ---------------------
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=True)
    billable = Column(Boolean, default=False)
    status = Column(String, default=TaskStatus.new.value)

    # link to client
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client = relationship("Client", back_populates="tasks")

    # who created
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    creator = relationship("User", foreign_keys=[created_by])

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ---------------------
    # Recurrence fields
    # ---------------------
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String, nullable=True)            # "daily","weekly","monthly","quarterly","yearly"
    recurrence_interval = Column(Integer, nullable=True)
    recurrence_weekday = Column(Integer, nullable=True)        # 0=Mon..6=Sun
    recurrence_day_of_month = Column(Integer, nullable=True)   # 1-31
    recurrence_end_date = Column(DateTime, nullable=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # Title templating & generation mode
    title_template = Column(String, nullable=True)             # e.g. "{title} - {month_name} {year}"
    generation_mode = Column(String, default="on_completion")  # default "on_completion"

    # ---------------------
    # Relationships
    # ---------------------
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="task_tags", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id], uselist=False)


class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    role = Column(String, default="assignee")  # assignee, reviewer, etc.

    user = relationship("User", back_populates="task_assignments")
    task = relationship("Task", back_populates="assignments")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="subtasks")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    tasks = relationship("Task", secondary="task_tags", back_populates="tags")


class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)


# ---------------------------------------------------------
# AUDIT LOG
# ---------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)              # e.g. "task_created", "login", "client_updated"
    entity_type = Column(String, nullable=False)         # "task", "client", "user", etc.
    entity_id = Column(Integer, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Optional details (JSON)
    details = Column(JSON, nullable=True)

    user = relationship("User", backref="audit_logs")