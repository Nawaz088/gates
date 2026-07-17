"""Create sessions table.

Revision ID: 0002
Revises: 0001
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("client_id", sa.String(255), nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("active_org_id", sa.String(24), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_status_expire", "sessions", ["status", "expire_at"])


def downgrade() -> None:
    op.drop_table("sessions")
