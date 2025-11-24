"""Add recurrence template fields (SQLite-safe rewrite)

Revision ID: 02dcbfca4329
Revises: 960dab935352
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '02dcbfca4329'
down_revision: Union[str, Sequence[str], None] = '960dab935352'
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Rebuild AUDIT_LOGS table safely for SQLite
    # ---------------------------------------------------------

    # Create new table with correct schema (matching models.py)
    op.create_table(
        "audit_logs_new",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("performed_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("timestamp", sa.DateTime),
        sa.Column("details", sa.JSON, nullable=True),
    )

    # Copy data from old table
    op.execute("""
        INSERT INTO audit_logs_new (
            id, action, entity_type, entity_id, performed_by, timestamp, details
        )
        SELECT
            id,
            action,
            entity_type,
            entity_id,
            performed_by,
            timestamp,
            details
        FROM audit_logs
    """)


    # Drop old table
    op.drop_table("audit_logs")

    # Rename new table
    op.rename_table("audit_logs_new", "audit_logs")

    # ---------------------------------------------------------
    # 2. Update TASKS table (simple, no rebuild needed)
    # ---------------------------------------------------------

    op.add_column("tasks", sa.Column("title_template", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("generation_mode", sa.String(), nullable=True))

    # Fix incorrect VARCHAR weekday column ? Integer
    op.execute("""
        ALTER TABLE tasks
        RENAME TO tasks_old
    """)

    # Rebuild tasks table with corrected schema
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("due_date", sa.DateTime),
        sa.Column("billable", sa.Boolean),
        sa.Column("status", sa.String),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id")),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("is_recurring", sa.Boolean),
        sa.Column("recurrence_rule", sa.String),
        sa.Column("recurrence_interval", sa.Integer),
        sa.Column("recurrence_weekday", sa.Integer),
        sa.Column("recurrence_day_of_month", sa.Integer),
        sa.Column("recurrence_end_date", sa.DateTime),
        sa.Column("parent_task_id", sa.Integer, sa.ForeignKey("tasks.id")),
        sa.Column("title_template", sa.String),
        sa.Column("generation_mode", sa.String),
    )

    op.execute("""
        INSERT INTO tasks (
            id, title, description, due_date, billable, status,
            client_id, created_by, created_at, updated_at,
            is_recurring, recurrence_rule, recurrence_interval,
            recurrence_weekday, recurrence_day_of_month,
            recurrence_end_date, parent_task_id,
            title_template, generation_mode
        )
        SELECT
            id, title, description, due_date, billable, status,
            client_id, created_by, created_at, updated_at,
            is_recurring, recurrence_rule, recurrence_interval,
            CASE
                WHEN typeof(recurrence_weekday)='text'
                THEN NULL
                ELSE recurrence_weekday
            END,
            recurrence_day_of_month,
            recurrence_end_date,
            parent_task_id,
            title_template, generation_mode
        FROM tasks_old
    """)

    op.drop_table("tasks_old")


def downgrade():
    raise NotImplementedError("Downgrade not supported for SQLite rebuild migrations.")