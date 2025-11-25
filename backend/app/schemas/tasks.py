# backend/app/schemas/tasks.py
# ---------------------
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

# ---------------------
# Recurrence enum
# ---------------------
class RecurrenceRule(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

# ---------------------
# Subtask schemas
# ---------------------
class SubtaskBase(BaseModel):
    title: str
    completed: Optional[bool] = False

class SubtaskCreate(SubtaskBase):
    pass

class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

class SubtaskOut(SubtaskBase):
    id: int
    task_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True

# ---------------------
# Assignment schemas
# ---------------------
class TaskAssignmentBase(BaseModel):
    user_id: int
    role: str = "assignee"

class TaskAssignmentCreate(TaskAssignmentBase):
    pass

class TaskAssignmentOut(TaskAssignmentBase):
    id: int
    class Config:
        orm_mode = True

# ---------------------
# Tag output
# ---------------------
class TagOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

# ---------------------
# Task schemas
# ---------------------
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    billable: bool = False
    status: Optional[str] = None

    # Recurrence
    is_recurring: bool = False
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_interval: Optional[int] = None
    recurrence_weekday: Optional[int] = None
    recurrence_day_of_month: Optional[int] = None
    recurrence_end_date: Optional[date] = None

    # Templating
    title_template: Optional[str] = None
    generation_mode: Optional[str] = "on_completion"

class TaskCreate(TaskBase):
    client_id: int
    assigned_users: Optional[List[int]] = None
    subtasks: Optional[List[SubtaskCreate]] = None
    tags: Optional[List[str]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    billable: Optional[bool] = None

    # Recurrence updates
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_interval: Optional[int] = None
    recurrence_weekday: Optional[int] = None
    recurrence_day_of_month: Optional[int] = None
    recurrence_end_date: Optional[date] = None

    title_template: Optional[str] = None
    generation_mode: Optional[str] = None

class TaskOut(TaskBase):
    id: int
    client_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    subtasks: List[SubtaskOut] = []
    assignments: List[TaskAssignmentOut] = []
    tags: List[TagOut] = []

    class Config:
        orm_mode = True
