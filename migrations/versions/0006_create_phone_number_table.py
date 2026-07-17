"""Create phone_number table.

Revision ID: 0006
Revises: 0005
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "phone_number",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("default_two_factor", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("linked_to", sa.String(24), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_phone_number_user", "phone_number", ["user_id"])
    op.create_index("ix_phone_number_number", "phone_number", ["phone_number"])


def downgrade() -> None:
    op.drop_table("phone_number")
