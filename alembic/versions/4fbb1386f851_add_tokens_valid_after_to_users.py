"""add tokens_valid_after to users

Revision ID: 4fbb1386f851
Revises: 261bbc4a9db4
Create Date: 2026-08-22 16:30:56.128955

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4fbb1386f851"
down_revision: Union[str, Sequence[str], None] = "261bbc4a9db4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("tokens_valid_after", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "tokens_valid_after")
