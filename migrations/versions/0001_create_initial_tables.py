"""Create initial tables: instance, users, email_address.

Revision ID: 0001
Revises:
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instance",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, server_default="default"),
        sa.Column("environment", sa.String(20), nullable=False, server_default="development"),
        sa.Column("auth_config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("branding", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("username", sa.String(32), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("has_image", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("primary_email_id", sa.String(24), nullable=True),
        sa.Column("primary_phone_id", sa.String(24), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("two_factor_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("banned", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ban_reason", sa.String(255), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("public_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("private_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("unsafe_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("last_sign_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_instance_id", "users", ["instance_id"])
    op.create_index("ix_users_email", "users", ["username"], postgresql_using="hash")

    op.create_table(
        "email_address",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("verification_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_to", sa.String(24), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_address_email", "email_address", ["email"])
    op.create_index("ix_email_address_user_id", "email_address", ["user_id"])


def downgrade() -> None:
    op.drop_table("email_address")
    op.drop_table("users")
    op.drop_table("instance")
