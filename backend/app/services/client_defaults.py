from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import List

from backend.app.crud_utils import tasks as task_crud
from backend.app.schemas.tasks import RecurrenceRule, TaskCreate


def _next_month_due(day: int) -> datetime:
    today = date.today()
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1

    last_day = monthrange(year, month)[1]
    day = min(day, last_day)

    return datetime(year, month, day)


def create_standard_client_tasks(db, client_id: int, creator_id: int) -> List[int]:
    """Create the standard recurring tasks for a new client.

    Returns a list of created task IDs.
    """

    task_templates = [
        {"title": "Complete bank feeds", "day_of_month": 5},
        {"title": "Reconcile accounts", "day_of_month": 10},
        {"title": "Send questions", "day_of_month": 15},
        {"title": "Send reports", "day_of_month": 25},
    ]

    created_task_ids: List[int] = []

    for template in task_templates:
        due_dt = _next_month_due(template["day_of_month"])

        task_payload = TaskCreate(
            title=template["title"],
            description=None,
            client_id=client_id,
            due_date=due_dt,
            billable=False,
            status="new",
            is_recurring=True,
            recurrence_rule=RecurrenceRule.monthly,
            recurrence_interval=1,
            recurrence_day_of_month=template["day_of_month"],
            recurrence_end_date=None,
            title_template="{title} - {month_name} {year}",
            generation_mode="on_completion",
            assigned_users=None,
            subtasks=None,
            tags=None,
        )

        task = task_crud.create_task(db, task_payload, creator_id=creator_id)
        created_task_ids.append(task.id)

    return created_task_ids
