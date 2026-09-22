"""add role to users

Revision ID: 982450d17068
Revises: 5098d758c71c
Create Date: 2026-09-22 11:40:20.658860

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "982450d17068"
down_revision: Union[str, Sequence[str], None] = "5098d758c71c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
    )
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('user', 'admin')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
