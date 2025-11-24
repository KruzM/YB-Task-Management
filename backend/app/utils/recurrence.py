# backend/app/utils/recurrence.py
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional

def next_occurrence(base: datetime, frequency: str, interval: int = 1,
                    weekday: Optional[str] = None,
                    day_of_month: Optional[int] = None) -> datetime:
    """
    Return the next occurrence datetime based on a base datetime and recurrence rule.
    frequency: "daily" | "weekly" | "monthly" | "yearly"
    interval: integer (every N units)
    weekday: optional weekday name lower-case ("monday", "tuesday"...). Used for weekly rules.
    day_of_month: integer day of month for monthly rules (1-31).
    """
    if frequency == "daily":
        return base + relativedelta(days=interval)
    if frequency == "weekly":
        # If weekday provided, compute next date for that weekday
        if weekday:
            # convert weekday to 0-6 (mon=0)
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            try:
                target = weekdays.index(weekday.lower())
            except ValueError:
                # fallback to interval-weeks from base
                return base + relativedelta(weeks=interval)
            # find next target weekday after base
            days_ahead = (target - base.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7 * interval
            else:
                # if we want every N weeks we move forward interval-1 more weeks
                days_ahead += 7 * (interval - 1)
            return base + relativedelta(days=days_ahead)
        else:
            return base + relativedelta(weeks=interval)
    if frequency == "monthly":
        if day_of_month:
            # try to produce same day next months
            candidate = base + relativedelta(months=interval)
            # if day doesn't exist (Feb 30), relativedelta will clamp, but we'll try to set day explicitly
            try:
                return candidate.replace(day=day_of_month)
            except Exception:
                # fallback: use last day of month
                from calendar import monthrange
                y = candidate.year
                m = candidate.month
                last = monthrange(y, m)[1]
                return candidate.replace(day=min(day_of_month, last))
        else:
            return base + relativedelta(months=interval)
    if frequency == "yearly":
        return base + relativedelta(years=interval)
    # default fallback
    return base + relativedelta(days=interval)