from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import User

from backend.app.schemas.tasks import (
    TaskCreate,
    TaskUpdate,
    TaskOut,
    SubtaskCreate,
    SubtaskUpdate,
    SubtaskOut,
    TodayDashboard,
    AdminUserTaskSummary,
)

# All task logic lives here
from backend.app.crud_utils import tasks as task_crud

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ---------------------------------------------------
# CREATE TASK
# ---------------------------------------------------
@router.post("/", response_model=TaskOut)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = task_crud.create_task(db, task_data, creator_id=current_user.id)
    return task


# ---------------------------------------------------
# LIST TASKS
# ---------------------------------------------------
@router.get("/", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

    statuses: Optional[str] = None,
    client_id: Optional[int] = None,
    assigned_user_id: Optional[int] = None,
    billable: Optional[bool] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,

    search: Optional[str] = None,

    sort_by: Optional[str] = "created_at",
    sort_dir: Optional[str] = "desc",
):
    return task_crud.list_tasks(
        db=db,
        statuses=statuses,
        client_id=client_id,
        assigned_user_id=assigned_user_id,
        billable=billable,
        due_before=due_before,
        due_after=due_after,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/dashboard/today", response_model=TodayDashboard)
def today_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    one_off, recurring = task_crud.tasks_due_today_for_user(db, current_user.id)
    return TodayDashboard(one_off_tasks=one_off, recurring_tasks=recurring)


@router.get("/queue/waiting", response_model=List[TaskOut])
def waiting_on_client_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_crud.waiting_on_client_queue(db, user_id=current_user.id)


@router.get("/dashboard/admin", response_model=List[AdminUserTaskSummary])
def admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return task_crud.admin_overview_by_user(db)


@router.get("/by-client/{client_id}/assignee/{user_id}", response_model=List[TaskOut])
def tasks_for_client_and_user(
    client_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_crud.tasks_for_client_and_user(db, client_id=client_id, user_id=user_id)


# ---------------------------------------------------
# KANBAN VIEW
# ---------------------------------------------------
@router.get("/kanban")
def get_kanban_board(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return task_crud.kanban_board(db)


# ---------------------------------------------------
# GET SINGLE TASK
# ---------------------------------------------------
@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------
# UPDATE TASK
# ---------------------------------------------------
@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    updates: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    # Detect completion ? use special behavior
    if updates.status == "completed":
        result = task_crud.mark_task_completed(db, task_id, actor_id=current_user.id)
        return result["task"]

    updated = task_crud.update_task(db, task_id, updates, actor_id=current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated


# Fallback full update route (PUT)
@router.put("/{task_id}", response_model=TaskOut)
def update_task_put(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.status == "completed":
        result = task_crud.mark_task_completed(db, task_id, actor_id=current_user.id)
        return result["task"]

    return task_crud.update_task(db, task_id, payload, actor_id=current_user.id)


# ---------------------------------------------------
# DELETE TASK
# ---------------------------------------------------
@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = task_crud.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return


# ---------------------------------------------------
# ASSIGN USERS
# ---------------------------------------------------
@router.post("/{task_id}/assign/{user_id}")
def assign_user_to_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    assignment = task_crud.add_user_to_task(
        db, task_id, user_id, performed_by=current_user.id
    )
    return {"message": "User assigned", "assignment_id": assignment.id}


@router.delete("/{task_id}/assign/{user_id}")
def remove_user_from_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = task_crud.remove_user_from_task(
        db, task_id, user_id, performed_by=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "User removed"}


# ---------------------------------------------------
# SUBTASKS
# ---------------------------------------------------
@router.post("/{task_id}/subtasks", response_model=SubtaskOut)
def add_subtask(
    task_id: int,
    subtask_data: SubtaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return task_crud.add_subtask(db, task_id, subtask_data, performed_by=current_user.id)


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(
    subtask_id: int,
    updates: SubtaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated = task_crud.update_subtask(
        db,
        subtask_id,
        title=updates.title,
        completed=updates.completed,
        performed_by=current_user.id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return updated


@router.delete("/subtasks/{subtask_id}", status_code=204)
def delete_subtask(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = task_crud.delete_subtask(db, subtask_id, performed_by=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return