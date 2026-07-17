"""Create verification table.

Revision ID: 0005
Revises: 0004
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "verification",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("user_id", sa.String(24), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=True),
        sa.Column("token_hash", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("extra_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_verification_target", "verification", ["target"])


def downgrade() -> None:
    op.drop_table("verification")
