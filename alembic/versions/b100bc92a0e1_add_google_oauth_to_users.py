"""add google oauth to users

Revision ID: b100bc92a0e1
Revises: 982450d17068
Create Date: 2026-09-23 11:48:47.499696

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b100bc92a0e1"
down_revision: Union[str, Sequence[str], None] = "982450d17068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("google_id", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])
    op.alter_column("users", "password_hash", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "password_hash", existing_type=sa.Text(), nullable=False)
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.drop_column("users", "google_id")
