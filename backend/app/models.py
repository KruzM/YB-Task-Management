from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="employee")

    client_assignments = relationship("ClientAssignment", back_populates="user")
    task_assignments = relationship("TaskAssignment", back_populates="user")


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
    client_id = Column(Integer, ForeignKey("clients.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="new")
    due_date = Column(String)
    billable = Column(Boolean, default=False)

    client = relationship("Client", back_populates="tasks")
    subtasks = relationship("Subtask", back_populates="task")
    assignments = relationship("TaskAssignment", back_populates="task")


class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)

    user = relationship("User", back_populates="task_assignments")
    task = relationship("Task", back_populates="assignments")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

    task = relationship("Task", back_populates="subtasks")