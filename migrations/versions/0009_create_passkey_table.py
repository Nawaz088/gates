"""Create passkey table.

Revision ID: 0009
Revises: 0008
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "passkey",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("credential_id", sa.LargeBinary, unique=True, nullable=False),
        sa.Column("public_key", sa.LargeBinary, nullable=False),
        sa.Column("sign_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("transports", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("aaguid", sa.String(36), nullable=True),
        sa.Column("backup_eligible", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("backup_state", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_passkey_user", "passkey", ["user_id"])


def downgrade() -> None:
    op.drop_table("passkey")
