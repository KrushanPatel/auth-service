"""create rate_limits table

Revision ID: d02419754cc4
Revises: 4fbb1386f851
Create Date: 2026-08-22 16:40:25.174126

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d02419754cc4"
down_revision: Union[str, Sequence[str], None] = "4fbb1386f851"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rate_limits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "window_start",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("key", "action", name="uq_rate_limits_key_action"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("rate_limits")
