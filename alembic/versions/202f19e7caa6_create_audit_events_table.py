"""create audit_events table

Revision ID: 202f19e7caa6
Revises: c73e4cb39f0b
Create Date: 2026-09-25 06:41:12.804419

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "202f19e7caa6"
down_revision: Union[str, Sequence[str], None] = "c73e4cb39f0b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EVENT_TYPES = (
    "login_success",
    "login_failure",
    "logout",
    "refresh_token_reuse_detected",
    "password_reset_completed",
    "mfa_enabled",
    "mfa_disabled",
    "role_changed",
    "oauth_account_linked",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("ip", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "event_type IN (" + ", ".join(f"'{t}'" for t in EVENT_TYPES) + ")",
            name="ck_audit_events_event_type",
        ),
    )
    op.create_index(
        "ix_audit_events_user_id_created_at",
        "audit_events",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_audit_events_event_type_created_at",
        "audit_events",
        ["event_type", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_audit_events_event_type_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_user_id_created_at", table_name="audit_events")
    op.drop_table("audit_events")
