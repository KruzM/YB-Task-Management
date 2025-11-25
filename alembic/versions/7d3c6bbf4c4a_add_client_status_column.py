"""Add status column to clients table

Revision ID: 7d3c6bbf4c4a
Revises: 02dcbfca4329
Create Date: 2025-11-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7d3c6bbf4c4a'
down_revision: Union[str, Sequence[str], None] = '02dcbfca4329'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status column with default value for existing records."""
    with op.batch_alter_table('clients') as batch_op:
        batch_op.add_column(
            sa.Column('status', sa.String(), nullable=True, server_default='active')
        )

    # Ensure any existing rows get the default value
    op.execute("UPDATE clients SET status = 'active' WHERE status IS NULL")


def downgrade() -> None:
    """Remove status column from clients table."""
    with op.batch_alter_table('clients') as batch_op:
        batch_op.drop_column('status')