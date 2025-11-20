from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from sqlalchemy import or_, asc, desc
from backend.app import models
from backend.app.models import Task, TaskAssignment, Tag
from backend.app.schemas.tasks import (
    TaskCreate, TaskUpdate, SubtaskCreate
)
from backend.app.models import TaskTag

# ---------------------------------------------------
# CREATE TASK
# ---------------------------------------------------

def create_task(db: Session, data: TaskCreate, creator_id: int):
    # 1. Create the base task and persist to get an ID
    new_task = models.Task(
        title=data.title,
        description=data.description,
        client_id=data.client_id,
        due_date=data.due_date,
        billable=data.billable,
        status=data.status or "new",
        created_by=creator_id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 2. Attach tags (create tags if they don't exist)
    if getattr(data, "tags", None):
        for tag_name in data.tags:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
                db.flush()  # ensure tag.id exists
            new_task.tags.append(tag)

    # 3. Assign Users
    for user_id in data.assigned_users or []:
        assignment = models.TaskAssignment(
            task_id=new_task.id,
            user_id=user_id,
            role="assignee"
        )
        db.add(assignment)

    # 4. Create Subtasks
    for sub in data.subtasks or []:
        subtask = models.Subtask(
            task_id=new_task.id,
            title=sub.title,
            completed=sub.completed
        )
        db.add(subtask)

    db.commit()
    db.refresh(new_task)

    return new_task


# ---------------------------------------------------
# GET TASK / LIST TASKS
# ---------------------------------------------------

def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def list_tasks(
    db: Session,
    statuses: Optional[str] = None,
    client_id: Optional[int] = None,
    assigned_user_id: Optional[int] = None,
    billable: Optional[bool] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_dir: Optional[str] = "desc",
):
    query = db.query(Task)

    # ---- FILTERING ----
    if statuses:
        status_list = [s.strip() for s in statuses.split(",") if s.strip()]
        if status_list:
            query = query.filter(Task.status.in_(status_list))

    if client_id:
        query = query.filter(Task.client_id == client_id)

    if billable is not None:
        query = query.filter(Task.billable == billable)

    if due_before:
        query = query.filter(Task.due_date <= due_before)

    if due_after:
        query = query.filter(Task.due_date >= due_after)

    if assigned_user_id:
        # join against TaskAssignment relationship
        query = query.join(Task.assignments).filter(TaskAssignment.user_id == assigned_user_id)

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.join(Task.tags).filter(models.Tag.name.in_(tag_list))

    # ---- SEARCH ----
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )

    # ---- SORTING ----
    # safe getattr: fallback to created_at
    sort_column = getattr(Task, sort_by, Task.created_at)

    if sort_dir == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    return query.all()


# ---------------------------------------------------
# UPDATE TASK
# ---------------------------------------------------

def update_task(db: Session, task_id: int, data: TaskUpdate):
    task = get_task(db, task_id)
    if not task:
        return None

    update_data = data.dict(exclude_unset=True)
    # handle tags specially if present in update_data (optional)
    if "tags" in update_data:
        # replace tags relationship with provided list
        new_tags = []
        for tag_name in update_data.pop("tags") or []:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
                db.flush()
            new_tags.append(tag)
        task.tags = new_tags

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


# ---------------------------------------------------
# DELETE TASK
# ---------------------------------------------------

def delete_task(db: Session, task_id: int):
    task = get_task(db, task_id)
    if not task:
        return False

    db.delete(task)
    db.commit()
    return True


# ---------------------------------------------------
# MANAGE ASSIGNMENTS
# ---------------------------------------------------

def add_user_to_task(db: Session, task_id: int, user_id: int, role: str = "assignee"):
    assignment = models.TaskAssignment(
        task_id=task_id,
        user_id=user_id,
        role=role
    )
    db.add(assignment)
    db.commit()
    return assignment


def remove_user_from_task(db: Session, task_id: int, user_id: int):
    assignment = (
        db.query(models.TaskAssignment)
        .filter(
            models.TaskAssignment.task_id == task_id,
            models.TaskAssignment.user_id == user_id
        )
        .first()
    )

    if not assignment:
        return False

    db.delete(assignment)
    db.commit()
    return True


# ---------------------------------------------------
# MANAGE SUBTASKS
# ---------------------------------------------------

def add_subtask(db: Session, task_id: int, data: SubtaskCreate):
    subtask = models.Subtask(
        task_id=task_id,
        title=data.title,
        completed=data.completed
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


def update_subtask(db: Session, subtask_id: int, title=None, completed=None):
    subtask = (
        db.query(models.Subtask)
        .filter(models.Subtask.id == subtask_id)
        .first()
    )
    if not subtask:
        return None

    if title is not None:
        subtask.title = title
    if completed is not None:
        subtask.completed = completed

    db.commit()
    db.refresh(subtask)
    return subtask


def delete_subtask(db: Session, subtask_id: int):
    subtask = (
        db.query(models.Subtask)
        .filter(models.Subtask.id == subtask_id)
        .first()
    )
    if not subtask:
        return False

    db.delete(subtask)
    db.commit()
    return True

def kanban_board(db: Session):
    # Fetch all tasks
    tasks = db.query(Task).all()

    board = {
        "new": [],
        "in_progress": [],
        "review": [],
        "completed": []
    }

    for task in tasks:
        status = task.status or "new"

        # If unexpected status, drop into "new"
        if status not in board:
            status = "new"

        board[status].append(task)

    return board