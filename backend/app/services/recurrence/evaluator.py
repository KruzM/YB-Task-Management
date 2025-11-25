# ---------------------
# Recurrence Evaluator
# ---------------------
from __future__ import annotations
from sqlalchemy.orm import Session

from .generator import create_next_recurring_task


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

    # All subtasks must be completed first
    for st in task_instance.subtasks:
        if not st.completed:
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
    if notification_hook:
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
