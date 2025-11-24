# ---------------------
# Recurrence helper utilities (date math + templating)
# ---------------------
from datetime import datetime
from calendar import monthrange
from dateutil.relativedelta import relativedelta

# ---------------------
# Date helpers
# ---------------------
def add_days(dt: datetime, days: int):
    return dt + relativedelta(days=days)

def add_weeks(dt: datetime, weeks: int):
    return dt + relativedelta(weeks=weeks)

def add_months_preserve_day(dt: datetime, months: int, day_of_month: int | None = None):
    candidate = dt + relativedelta(months=months)
    if day_of_month:
        y = candidate.year
        m = candidate.month
        last = monthrange(y, m)[1]
        day = min(day_of_month, last)
        return candidate.replace(day=day)
    try:
        return candidate.replace(day=dt.day)
    except Exception:
        y = candidate.year
        m = candidate.month
        last = monthrange(y, m)[1]
        return candidate.replace(day=last)

def add_years(dt: datetime, years: int):
    try:
        return dt.replace(year=dt.year + years)
    except Exception:
        # fallback: use relativedelta (handles leap days more gracefully)
        return dt + relativedelta(years=years)

def last_day_of_month(dt: datetime):
    y = dt.year
    m = dt.month
    last = monthrange(y, m)[1]
    return dt.replace(day=last)

# ---------------------
# Templating helper
# ---------------------
def render_title(template: str | None, base_title: str, next_due: datetime, recurrence_rule: str) -> str:
    # sensible defaults when template not provided
    if not template:
        if recurrence_rule in ("monthly", "quarterly", "yearly"):
            template = "{title} - {month_name} {year}"
        else:
            template = "{title} - {cycle}"

    month_name = next_due.strftime("%B")
    month = next_due.month
    year = next_due.year
    quarter = (next_due.month - 1) // 3 + 1

    # cycle string
    if recurrence_rule == "weekly":
        cycle = next_due.strftime("%Y-%m-%d")
    elif recurrence_rule == "daily":
        cycle = next_due.strftime("%Y-%m-%d")
    elif recurrence_rule == "monthly":
        cycle = f"{month_name} {year}"
    elif recurrence_rule == "quarterly":
        cycle = f"Q{quarter} {year}"
    elif recurrence_rule == "yearly":
        cycle = f"{year}"
    else:
        cycle = next_due.strftime("%Y-%m-%d")

    rendered = template.replace("{title}", base_title)
    rendered = rendered.replace("{month_name}", month_name)
    rendered = rendered.replace("{month}", str(month))
    rendered = rendered.replace("{year}", str(year))
    rendered = rendered.replace("{quarter}", f"Q{quarter}")
    rendered = rendered.replace("{cycle}", cycle)
    return rendered