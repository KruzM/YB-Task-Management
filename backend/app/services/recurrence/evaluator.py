# ---------------------
# High-level recurrence runner and utilities
# ---------------------
from typing import List
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.services.recurrence.generator import generate_next_task

# This runner can be used by a router or a background task to process completions or scheduled checks.
def run_generate_for_completed_task(db: Session, completed_task_id: int):
    task = db.query(models.Task).filter(models.Task.id == completed_task_id).first()
    if not task:
        return {"created": 0, "ids": []}
    created = generate_next_task(db, task)
    return {"created": (1 if created else 0), "ids": [created.id] if created else []}

# For batch processing (if needed) - not required for on-complete generation but helpful
def run_for_all_due_or_pending(db: Session):
    """
    Example: find all recurring tasks flagged with some marker or in a state expecting new generation.
    Not used for on-completion flow, but kept for compatibility.
    """
    results = {"created": 0, "ids": []}
    # placeholder
    return results