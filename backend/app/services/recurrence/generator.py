# ---------------------
# Recurrence Generator
# ---------------------
from __future__ import annotations
from datetime import date, datetime

from sqlalchemy.orm import Session

from .helpers import next_due_for_rule, to_date


# ---------------------
# Clone task core fields (adapted to YOUR Task model)
# ---------------------
def _clone_task_fields(src_task):
    return {
        "title": src_task.title,
        "description": src_task.description,
        "client_id": src_task.client_id,
        "billable": src_task.billable,
        "created_by": src_task.created_by,

        # Recurrence fields
        "is_recurring": src_task.is_recurring,
        "recurrence_rule": src_task.recurrence_rule,
        "recurrence_interval": src_task.recurrence_interval,
        "recurrence_weekday": src_task.recurrence_weekday,
        "recurrence_day_of_month": src_task.recurrence_day_of_month,
        "generation_mode": src_task.generation_mode,

        # Link chain of recurring tasks
        "parent_task_id": src_task.parent_task_id or src_task.id,
    }
    


# ---------------------
# Main: create next recurring task
# ---------------------
def create_next_recurring_task(
    db: Session,
    task_model,
    subtask_model,
    src_task,
    *,
    recurrence_rule: dict,
    commit: bool = True
):
    """
    Creates the next task instance after completion of src_task.
    """

    # Determine last event date
    last_date = (
        getattr(src_task, "completed_at", None)
        or getattr(src_task, "due_date", None)
        or date.today()
    )
    last_date = to_date(last_date)

    # Compute new due date
    next_due = next_due_for_rule(
        last_date,
        recurrence_rule.get("type", "monthly"),
        assigned_weekday=recurrence_rule.get("assigned_weekday"),
        day_of_month=recurrence_rule.get("day_of_month"),
        every=recurrence_rule.get("every", 1),
    )

    # Respect recurrence end-date cutoff
    recurrence_end = to_date(getattr(src_task, "recurrence_end_date", None))
    if recurrence_end and next_due > recurrence_end:
        return None


    # Clone fields
    new_task_data = _clone_task_fields(src_task)
    new_task_data.update({
        "due_date": next_due,
        "status": "new",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    # Create task
    new_task = task_model(**new_task_data)
    db.add(new_task)
    db.flush()   # Get new_task.id

    # ---------------------
    # Clone subtasks (your model: Subtask has title + completed)
    # ---------------------
    for st in src_task.subtasks:
        subtask_data = {
            "task_id": new_task.id,
            "title": st.title,
            "completed": False,       # reset
        }
        new_sub = subtask_model(**subtask_data)
        db.add(new_sub)

    if commit:
        db.commit()
        db.refresh(new_task)

    return new_task
