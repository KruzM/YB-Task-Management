from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import crud
from backend.app.schemas.tasks import (
    TaskCreate,
    TaskUpdate,
    TaskOut,
    SubtaskCreate,
    SubtaskUpdate,
    SubtaskOut,
)
from backend.app.auth import get_current_user
from typing import List, Optional
from backend.app.models import User
from datetime import datetime
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
    task = crud.tasks.create_task(db, task_data, creator_id=current_user.id)
    return task


# ---------------------------------------------------
# LIST TASKS
# ---------------------------------------------------

@router.get("/", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

    # FILTERS
    statuses: Optional[str] = None,
    client_id: Optional[int] = None,
    assigned_user_id: Optional[int] = None,
    billable: Optional[bool] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,

    # SEARCH
    search: Optional[str] = None,

    # SORTING
    sort_by: Optional[str] = "created_at",  # created_at, updated_at, due_date, title
    sort_dir: Optional[str] = "desc"        # asc or desc
):
    tasks = crud.tasks.list_tasks(
        db=db,
        status=status,
        client_id=client_id,
        assigned_user_id=assigned_user_id,
        billable=billable,
        due_before=due_before,
        due_after=due_after,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return tasks
# ---------------------------------------------------
# KANBAN VIEW
# ---------------------------------------------------

@router.get("/kanban")
def get_kanban_board(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    board = crud.tasks.kanban_board(db)
    return board

# ---------------------------------------------------
# GET SINGLE TASK
# ---------------------------------------------------

@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = crud.tasks.get_task(db, task_id)
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
    task = crud.tasks.update_task(db, task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------
# DELETE TASK
# ---------------------------------------------------

@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = crud.tasks.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return


# ---------------------------------------------------
# ASSIGN USERS TO TASK
# ---------------------------------------------------

@router.post("/{task_id}/assign/{user_id}")
def assign_user_to_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    assignment = crud.tasks.add_user_to_task(db, task_id, user_id)
    return {"message": "User assigned", "assignment_id": assignment.id}


@router.delete("/{task_id}/assign/{user_id}")
def remove_user_from_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = crud.tasks.remove_user_from_task(db, task_id, user_id)
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
    subtask = crud.tasks.add_subtask(db, task_id, subtask_data)
    return subtask


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(
    subtask_id: int,
    updates: SubtaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    updated = crud.tasks.update_subtask(
        db,
        subtask_id,
        title=updates.title,
        completed=updates.completed,
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
    deleted = crud.tasks.delete_subtask(db, subtask_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return