"""Create external_account table.

Revision ID: 0007
Revises: 0006
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_account",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("scopes", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("access_token_enc", sa.String(1024), nullable=True),
        sa.Column("refresh_token_enc", sa.String(1024), nullable=True),
        sa.Column("id_token_enc", sa.String(2048), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("passwordless", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_external_account_user", "external_account", ["user_id"])
    op.create_unique_constraint(
        "uq_external_account_provider",
        "external_account",
        ["instance_id", "provider", "provider_user_id"],
    )


def downgrade() -> None:
    op.drop_table("external_account")
