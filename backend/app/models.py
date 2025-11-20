from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum



# =============================
# ROLE & PERMISSION MODELS
# =============================

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

class TaskStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    completed = "completed"


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

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    assigned_weekday = Column(String, nullable=False)

    assignments = relationship("ClientAssignment", back_populates="client")
    tasks = relationship("Task", back_populates="client")


class ClientAssignment(Base):
    __tablename__ = "client_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))

    user = relationship("User", back_populates="client_assignments")
    client = relationship("Client", back_populates="assignments")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text)

    status = Column(String, default=TaskStatus.new.value)
    due_date = Column(DateTime, nullable=True)

    billable = Column(Boolean, default=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="tasks")
    creator = relationship("User")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="task_tags", back_populates="tasks")

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
