# ---------------------
# Recurrence Helpers
# ---------------------
from __future__ import annotations
from datetime import date, datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta


# Convert datetime ? date
def to_date(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.date()
    return dt


# ---- Basic increments ----

def add_days(d: date, n: int):
    return d + timedelta(days=n)

def add_weeks(d: date, n: int):
    return d + timedelta(weeks=n)

def add_months(d: date, n: int):
    return d + relativedelta(months=n)

def add_years(d: date, n: int):
    return d + relativedelta(years=n)


# ---- Calendar helpers ----

def first_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """
    Returns first occurrence of weekday in a given month.
    weekday = 0 (Monday) ... 6 (Sunday)
    """
    cal = calendar.Calendar()
    for week in cal.monthdatescalendar(year, month):
        for d in week:
            if d.month == month and d.weekday() == weekday:
                return d
    # fallback
    return date(year, month, 1)


# ---- Core recurrence date logic ----

def next_due_for_rule(
    last_date: date,
    recurrence_type: str,
    *,
    every: int = 1,
    assigned_weekday: int | None = None,
    day_of_month: int | None = None
) -> date:
    """
    Computes the next due date for:
      - daily
      - weekly
      - monthly
      - quarterly
      - yearly

    Uses your Task model recurrence fields.
    """

    recurrence_type = recurrence_type.lower()
    step = every if every >= 1 else 1

    # ---- DAILY ----
    if recurrence_type == "daily":
        return add_days(last_date, step)

    # ---- WEEKLY ----
    if recurrence_type == "weekly":
        return add_weeks(last_date, step)

    # ---- MONTHLY ----
    if recurrence_type == "monthly":
        target = add_months(last_date, step)

        # If user specifies "use a specific weekday"
        if assigned_weekday is not None:
            return first_weekday_of_month(target.year, target.month, assigned_weekday)

        # Otherwise: use day_of_month if defined
        if day_of_month:
            last_day = calendar.monthrange(target.year, target.month)[1]
            return date(target.year, target.month, min(day_of_month, last_day))

        # Default: same day number
        last_day = calendar.monthrange(target.year, target.month)[1]
        return date(target.year, target.month, min(last_date.day, last_day))

    # ---- QUARTERLY ----
    if recurrence_type == "quarterly":
        target = add_months(last_date, step * 3)

        if assigned_weekday is not None:
            return first_weekday_of_month(target.year, target.month, assigned_weekday)

        if day_of_month:
            last_day = calendar.monthrange(target.year, target.month)[1]
            return date(target.year, target.month, min(day_of_month, last_day))

        last_day = calendar.monthrange(target.year, target.month)[1]
        return date(target.year, target.month, min(last_date.day, last_day))

    # ---- YEARLY ----
    if recurrence_type == "yearly":
        target = add_years(last_date, step)

        if assigned_weekday is not None:
            return first_weekday_of_month(target.year, target.month, assigned_weekday)

        if day_of_month:
            last_day = calendar.monthrange(target.year, target.month)[1]
            return date(target.year, target.month, min(day_of_month, last_day))

        last_day = calendar.monthrange(target.year, target.month)[1]
        return date(target.year, target.month, min(last_date.day, last_day))

    # Default fallback: daily
    return add_days(last_date, 1)
