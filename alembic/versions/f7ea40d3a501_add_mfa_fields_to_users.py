"""add mfa fields to users

Revision ID: f7ea40d3a501
Revises: 6feead7615a2
Create Date: 2026-09-16 22:45:40.005818

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7ea40d3a501"
down_revision: Union[str, Sequence[str], None] = "6feead7615a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("mfa_secret", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "mfa_enabled")
