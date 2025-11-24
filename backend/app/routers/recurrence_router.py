# backend/app/routers/recurrence_router.py
# ---------------------
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models
from backend.app.services.recurrence.generator import generate_on_completion
from backend.app.schemas.recurrence_schemas import RunResult

router = APIRouter(prefix="/recurrence", tags=["Recurrence"])

# Manual run for a single completed task (useful for testing)
@router.post("/run/{task_id}", response_model=RunResult)
def run_for_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    created = 0
    ids = []
    # We expect caller to pass a *completed* task_id (or a task that was just completed)
    if getattr(task, "is_recurring", False):
        new_task = generate_on_completion(db, task)
        if new_task:
            created = 1
            ids = [new_task.id]

    return {"created": created, "ids": ids}


# Convenience: run generation for all tasks that are marked completed and recurring
@router.post("/run-all", response_model=RunResult)
def run_all_completed_recurring(db: Session = Depends(get_db)):
    created = 0
    ids = []
    tasks = db.query(models.Task).filter(models.Task.is_recurring == True, models.Task.status == "completed").all()
    for t in tasks:
        new_task = generate_on_completion(db, t)
        if new_task:
            created += 1
            ids.append(new_task.id)
    return {"created": created, "ids": ids}