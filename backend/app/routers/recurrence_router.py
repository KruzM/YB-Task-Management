# backend/app/routers/recurrence_router.py
# ---------------------
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import models
from backend.app.schemas.recurrence_schemas import RunResult
from backend.app.services.recurrence.evaluator import evaluate_task_for_recurrence

router = APIRouter(prefix="/recurrence", tags=["Recurrence"])


# ---------------------------------------------------
# Manually trigger recurrence for a single task
# ---------------------------------------------------
@router.post("/run/{task_id}", response_model=RunResult)
def run_for_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not getattr(task, "is_recurring", False):
        return {"created": 0, "ids": []}

    generated = evaluate_task_for_recurrence(
        db=db,
        task_model=models.Task,
        subtask_model=models.Subtask,
        task_instance=task,
        commit=True,
        notification_hook=None,  # or send_notification if you want
    )

    if generated:
        return {"created": 1, "ids": [generated.id]}

    return {"created": 0, "ids": []}


# ---------------------------------------------------
# Run recurrence for ALL completed recurring tasks
# ---------------------------------------------------
@router.post("/run-all", response_model=RunResult)
def run_all_completed_recurring(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).filter(
        models.Task.is_recurring == True,
        models.Task.status == "completed"
    ).all()

    created = 0
    ids = []

    for task in tasks:
        generated = evaluate_task_for_recurrence(
            db=db,
            task_model=models.Task,
            subtask_model=models.Subtask,
            task_instance=task,
            commit=True,
            notification_hook=None,
        )
        if generated:
            created += 1
            ids.append(generated.id)

    return {"created": created, "ids": ids}
