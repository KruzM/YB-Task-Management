from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# -----------------------
# SUBTASK SCHEMAS
# -----------------------

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
# ---------------------------
# TASK ASSIGNMENT SCHEMAS
# ---------------------------

class TaskAssignmentBase(BaseModel):
    user_id: int
    role: str = "assignee"


class TaskAssignmentCreate(TaskAssignmentBase):
    pass


class TaskAssignmentOut(TaskAssignmentBase):
    id: int

    class Config:
        orm_mode = True


# ---------------------------
# TASK SCHEMAS
# ---------------------------

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    billable: bool = False
    status: Optional[str] = None  # "new", "in_progress", etc.


class TaskCreate(TaskBase):
    client_id: int
    assigned_users: Optional[List[int]] = []  # user IDs
    subtasks: Optional[List[SubtaskCreate]] = []
    tags: Optional[List[str]] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    billable: Optional[bool] = None

class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

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