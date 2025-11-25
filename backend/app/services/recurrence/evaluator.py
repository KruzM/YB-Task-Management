# ---------------------
# Recurrence Evaluator
# ---------------------
from __future__ import annotations
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .generator import create_next_recurring_task
from .helpers import to_date


def evaluate_task_for_recurrence(
    db: Session,
    task_model,
    subtask_model,
    task_instance,
    *,
    commit: bool = True,
    notification_hook=None,
):
    """
    Runs when a task is completed.
    Checks:
      - is_recurring == True
      - all subtasks completed
      - then generates the next task in the series
    """

    # Not a recurring task? Nothing to do.
    if not getattr(task_instance, "is_recurring", False):
        return None

    # Only generate from the most recent task in the recurrence chain
    root_id = task_instance.parent_task_id or task_instance.id
    latest_task = (
        db.query(task_model)
        .filter(
            or_(
                task_model.id == root_id,
                task_model.parent_task_id == root_id,
            )
        )
        .order_by(task_model.due_date.desc().nullslast(), task_model.id.desc())
        .first()
    )

    if latest_task and latest_task.id != task_instance.id:
        return None

    # All subtasks must be completed first
    for st in task_instance.subtasks:
        if not st.completed:
            return None

    # Stop generating if recurrence end-date has been reached
    recurrence_end = to_date(getattr(task_instance, "recurrence_end_date", None))
    current_due = to_date(getattr(task_instance, "due_date", None))
    if recurrence_end and current_due and current_due >= recurrence_end:
        return None

    # Build recurrence_rule dict expected by generator
    recurrence_rule = {
        "type": task_instance.recurrence_rule,
        "every": task_instance.recurrence_interval or 1,
        "assigned_weekday": task_instance.recurrence_weekday,
        "day_of_month": task_instance.recurrence_day_of_month,
    }

    # Generate next instance
    new_task = create_next_recurring_task(
        db=db,
        task_model=task_model,
        subtask_model=subtask_model,
        src_task=task_instance,
        recurrence_rule=recurrence_rule,
        commit=commit
    )

    # Notify assigned user(s)
    if notification_hook and new_task:
        try:
            # Notify all assigned users
            for assign in task_instance.assignments:
                user_id = assign.user_id
                notification_hook(
                    user_id,
                    f"New recurring task created: {new_task.title} (due {new_task.due_date})",
                    task=new_task
                )
        except Exception:
            pass   # don't break task generation if notifications fail

    return new_task
