# backend/app/schemas/recurrence_schemas.py
# ---------------------
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# ---------------------
# Recurrence Enum
# ---------------------
class RecurrenceRule(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

# ---------------------
# Recurrence create/update schema 
# ---------------------
class RecurrenceConfig(BaseModel):
    is_recurring: Optional[bool] = False
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_interval: Optional[int] = 1
    recurrence_weekday: Optional[int] = None
    recurrence_day_of_month: Optional[int] = None
    recurrence_end_date: Optional[date] = None
    title_template: Optional[str] = None
    generation_mode: Optional[str] = "on_completion"

# ---------------------
# Run result
# ---------------------
class RunResult(BaseModel):
    created: int
    ids: List[int] = []