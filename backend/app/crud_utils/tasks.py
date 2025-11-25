from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime, date, time

from sqlalchemy import or_, asc, desc, func, case
from backend.app import models
from backend.app.models import Task, TaskAssignment, Tag, User
from backend.app.schemas.tasks import (
    TaskCreate, TaskUpdate, SubtaskCreate
)
from backend.app.models import TaskTag
from backend.app.crud_utils.audit import log_task_action
from backend.app.services.recurrence.evaluator import evaluate_task_for_recurrence
from backend.app.services.recurrence.notifications import send_notification

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
        created_by=creator_id,

        # ---------------------
        # Recurrence fields
        # ---------------------
        is_recurring=data.is_recurring,
        recurrence_rule=(
            data.recurrence_rule.value if data.recurrence_rule else None
        ),
        recurrence_interval=data.recurrence_interval,
        recurrence_weekday=data.recurrence_weekday,
        recurrence_day_of_month=data.recurrence_day_of_month,
        recurrence_end_date=data.recurrence_end_date,
        title_template=data.title_template,
        generation_mode=data.generation_mode,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    log_task_action(
        db,
        action="task_created",
        task_id=new_task.id,
        performed_by=creator_id,
        details={"title": new_task.title, "client_id": new_task.client_id},
    )

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

def update_task(db: Session, task_id: int, data: TaskUpdate, actor_id: Optional[int] = None):
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
    if actor_id:
        log_task_action(
            db,
            action="task_updated",
            task_id=task.id,
            performed_by=actor_id,
            details={"updated_fields": list(update_data.keys())},
        )
    return task


# ---------------------------------------------------
# DELETE TASK
# ---------------------------------------------------

def delete_task(db: Session, task_id: int):
    task = get_task(db, task_id)
    if not task:
        return False

    log_task_action(
        db,
        action="task_deleted",
        task_id=task_id,
        performed_by=task.created_by,
        details={"title": task.title},
    )
    db.delete(task)
    db.commit()
    return True


# ---------------------------------------------------
# MANAGE ASSIGNMENTS
# ---------------------------------------------------

def add_user_to_task(
    db: Session, task_id: int, user_id: int, role: str = "assignee", performed_by: Optional[int] = None
):
    assignment = models.TaskAssignment(
        task_id=task_id,
        user_id=user_id,
        role=role
    )
    db.add(assignment)
    db.commit()
    if performed_by:
        log_task_action(
            db,
            action="task_assigned",
            task_id=task_id,
            performed_by=performed_by,
            details={"assigned_user_id": user_id, "role": role},
        )
    return assignment


def remove_user_from_task(db: Session, task_id: int, user_id: int, performed_by: Optional[int] = None):
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
    if performed_by:
        log_task_action(
            db,
            action="task_unassigned",
            task_id=task_id,
            performed_by=performed_by,
            details={"removed_user_id": user_id},
        )
    return True


# ---------------------------------------------------
# MANAGE SUBTASKS
# ---------------------------------------------------

def add_subtask(db: Session, task_id: int, data: SubtaskCreate, performed_by: Optional[int] = None):
    subtask = models.Subtask(
        task_id=task_id,
        title=data.title,
        completed=data.completed
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    if performed_by:
        log_task_action(
            db,
            action="subtask_created",
            task_id=task_id,
            performed_by=performed_by,
            details={"subtask_id": subtask.id, "title": subtask.title},
        )
    return subtask


def update_subtask(db: Session, subtask_id: int, title=None, completed=None, performed_by: Optional[int] = None):
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
    if performed_by:
        log_task_action(
            db,
            action="subtask_updated",
            task_id=subtask.task_id,
            performed_by=performed_by,
            details={"subtask_id": subtask_id, "title": title, "completed": completed},
        )
    return subtask


def delete_subtask(db: Session, subtask_id: int, performed_by: Optional[int] = None):
    subtask = (
        db.query(models.Subtask)
        .filter(models.Subtask.id == subtask_id)
        .first()
    )
    if not subtask:
        return False

    db.delete(subtask)
    db.commit()
    if performed_by:
        log_task_action(
            db,
            action="subtask_deleted",
            task_id=subtask.task_id,
            performed_by=performed_by,
            details={"subtask_id": subtask_id},
        )
    return True


# ---------------------------------------------------
# TASK COMPLETION & RECURRENCE
# ---------------------------------------------------


def mark_task_completed(db: Session, task_id: int, actor_id: Optional[int] = None):
    """Mark a task completed and trigger recurrence if applicable."""

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None

    task.status = "completed"
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    if actor_id:
        log_task_action(
            db,
            action="task_completed",
            task_id=task.id,
            performed_by=actor_id,
            details={"title": task.title},
        )

    if not task.is_recurring:
        return {"task": task, "generated": None}

    generated = evaluate_task_for_recurrence(
        db=db,
        task_model=models.Task,
        subtask_model=models.Subtask,
        task_instance=task,
        commit=True,
        notification_hook=send_notification,
    )

    return {"task": task, "generated": generated}


# ---------------------------------------------------
# DASHBOARDS & VIEWS
# ---------------------------------------------------


def tasks_due_today_for_user(db: Session, user_id: int) -> Tuple[List[Task], List[Task]]:
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    base_query = (
        db.query(Task)
        .join(Task.assignments)
        .filter(
            TaskAssignment.user_id == user_id,
            Task.due_date >= start,
            Task.due_date <= end,
        )
    )

    one_off = base_query.filter(Task.is_recurring.is_(False)).all()
    recurring = base_query.filter(Task.is_recurring.is_(True)).all()
    return one_off, recurring


def waiting_on_client_queue(db: Session, user_id: Optional[int] = None) -> List[Task]:
    query = db.query(Task).filter(Task.status == "waiting_on_client")
    if user_id:
        query = query.join(Task.assignments).filter(TaskAssignment.user_id == user_id)
    return query.all()


def admin_overview_by_user(db: Session) -> List[dict]:
    rows = (
        db.query(
            TaskAssignment.user_id,
            func.coalesce(User.full_name, User.email).label("user_name"),
            func.count(Task.id).label("total"),
            func.count(case((Task.status == "completed", 1))).label("completed"),
            func.count(case((Task.status == "in_progress", 1))).label("in_progress"),
            func.count(case((Task.status == "waiting_on_client", 1))).label("waiting_on_client"),
            func.count(case((Task.status != "completed", 1))).label("open_tasks"),
        )
        .join(User, User.id == TaskAssignment.user_id)
        .join(Task, Task.id == TaskAssignment.task_id)
        .group_by(TaskAssignment.user_id, User.full_name, User.email)
        .all()
    )

    return [
        {
            "user_id": r.user_id,
            "user_name": r.user_name,
            "total_tasks": r.total,
            "open_tasks": r.open_tasks,
            "in_progress_tasks": r.in_progress,
            "waiting_on_client": r.waiting_on_client,
            "completed_tasks": r.completed,
        }
        for r in rows
    ]


def tasks_for_client_and_user(db: Session, client_id: int, user_id: int) -> List[Task]:
    return (
        db.query(Task)
        .join(Task.assignments)
        .filter(Task.client_id == client_id, TaskAssignment.user_id == user_id)
        .all()
    )

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