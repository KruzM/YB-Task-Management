# backend/app/services/recurrence/generator.py
# ---------------------------------------------------
# Recurrence Generation Engine (clean architecture)
# ---------------------------------------------------

from datetime import datetime
from sqlalchemy.orm import Session
from calendar import monthrange
from dateutil.relativedelta import relativedelta

from backend.app import models
from backend.app.models import TaskStatus

# ===================================================
# DATE HELPERS
# ===================================================

def _add_days(dt: datetime, days: int) -> datetime:
    return dt + relativedelta(days=days)

def _add_weeks(dt: datetime, weeks: int) -> datetime:
    return dt + relativedelta(weeks=weeks)

def _add_months_preserve_day(dt: datetime, months: int, day_of_month: int | None):
    candidate = dt + relativedelta(months=months)
    if day_of_month:
        y, m = candidate.year, candidate.month
        last = monthrange(y, m)[1]
        day = min(day_of_month, last)
        return candidate.replace(day=day)

    # handle months with fewer days gracefully
    try:
        return candidate.replace(day=dt.day)
    except ValueError:
        y, m = candidate.year, candidate.month
        last = monthrange(y, m)[1]
        return candidate.replace(day=last)

def _add_years(dt: datetime, years: int) -> datetime:
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt + relativedelta(years=years)

# ===================================================
# TEMPLATE RENDERING
# ===================================================

def _render_title(template, base_title, next_due: datetime, rule: str) -> str:
    if not template:
        if rule in ("monthly", "quarterly", "yearly"):
            template = "{title} - {month_name} {year}"
        else:
            template = "{title} - {cycle}"

    month_name = next_due.strftime("%B")
    quarter = (next_due.month - 1) // 3 + 1

    cycle_map = {
        "daily": next_due.strftime("%Y-%m-%d"),
        "weekly": next_due.strftime("%Y-%m-%d"),
        "monthly": f"{month_name} {next_due.year}",
        "quarterly": f"Q{quarter} {next_due.year}",
        "yearly": str(next_due.year)
    }

    cycle = cycle_map.get(rule, next_due.strftime("%Y-%m-%d"))

    out = template.replace("{title}", base_title)
    out = out.replace("{month_name}", month_name)
    out = out.replace("{year}", str(next_due.year))
    out = out.replace("{cycle}", cycle)
    return out

# ===================================================
# COMPUTE NEXT DUE DATE
# ===================================================

def _compute_next_due(current_due, rule, interval, weekday, day_of_month):
    base = current_due or datetime.utcnow()
    rule = (rule or "").lower()

    if rule == "daily":
        return _add_days(base, interval)
    if rule == "weekly":
        return _add_weeks(base, interval)
    if rule == "monthly":
        return _add_months_preserve_day(base, interval, day_of_month)
    if rule == "quarterly":
        return _add_months_preserve_day(base, 3 * interval, day_of_month)
    if rule == "yearly":
        return _add_years(base, interval)

    return _add_days(base, interval)

# ===================================================
# GENERATE THE NEXT TASK ON COMPLETION
# ===================================================

def generate_next_task(db: Session, completed_task: models.Task):
    if not completed_task.is_recurring:
        return None

    rule = completed_task.recurrence_rule
    if not rule:
        return None

    interval = completed_task.recurrence_interval or 1
    weekday = completed_task.recurrence_weekday
    dom = completed_task.recurrence_day_of_month
    end_dt = completed_task.recurrence_end_date

    next_due = _compute_next_due(completed_task.due_date, rule, interval, weekday, dom)

    if end_dt and next_due.date() > end_dt.date():
        return None

    new_title = _render_title(
        completed_task.title_template,
        completed_task.title,
        next_due,
        rule
    )

    child = models.Task(
        title=new_title,
        description=completed_task.description,
        due_date=next_due,
        billable=completed_task.billable,
        status=TaskStatus.new.value,
        client_id=completed_task.client_id,
        created_by=completed_task.created_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_recurring=completed_task.is_recurring,
        recurrence_rule=completed_task.recurrence_rule,
        recurrence_interval=completed_task.recurrence_interval,
        recurrence_weekday=completed_task.recurrence_weekday,
        recurrence_day_of_month=completed_task.recurrence_day_of_month,
        recurrence_end_date=completed_task.recurrence_end_date,
        parent_task_id=completed_task.id,
        title_template=completed_task.title_template,
        generation_mode=completed_task.generation_mode
    )

    db.add(child)
    db.commit()
    db.refresh(child)

    # copy assignments
    for a in completed_task.assignments:
        db.add(models.TaskAssignment(task_id=child.id, user_id=a.user_id, role=a.role))

    # copy subtasks (reset to not completed)
    for st in completed_task.subtasks:
        db.add(models.Subtask(task_id=child.id, title=st.title, completed=False))

    # copy tags
    for t in completed_task.tags:
        db.execute(
            "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (:task_id, :tag_id)",
            {"task_id": child.id, "tag_id": t.id}
        )

    db.commit()
    return child

def generate_on_completion(db: Session, completed_task: models.Task):
    return generate_next_task(db, completed_task)

# ===================================================
# BACKGROUND PASS � CHECK ALL COMPLETED RECURRING TASKS
# ===================================================

def run_recurrence_pass(db: Session):
    """
    Called by the scheduler.
    Looks for completed recurring tasks whose children have not yet been created.
    """

    tasks = (
        db.query(models.Task)
        .filter(models.Task.is_recurring.is_(True))
        .filter(models.Task.status == TaskStatus.completed.value)
        .all()
    )

    created = []

    for t in tasks:
        next_child = generate_next_task(db, t)
        if next_child:
            created.append(next_child)

    return {"created": len(created), "tasks": created}