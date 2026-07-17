"""Create jwt_template table.

Revision ID: 0014
Revises: 0013
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jwt_template",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("algorithm", sa.String(10), nullable=False, server_default="HS256"),
        sa.Column("lifetime", sa.Integer, nullable=False, server_default="3600"),
        sa.Column("claims", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("signing_key", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("jwt_template")
