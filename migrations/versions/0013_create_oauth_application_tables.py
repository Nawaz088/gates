"""Create oauth_application and oauth_consent tables.

Revision ID: 0013
Revises: 0012
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_application",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("client_id", sa.String(255), unique=True, nullable=False),
        sa.Column("client_secret_hash", sa.String(255), nullable=False),
        sa.Column("redirect_uris", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("scopes", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("homepage_url", sa.String(1024), nullable=True),
        sa.Column("logo_url", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "oauth_consent",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("oauth_application_id", sa.String(24), sa.ForeignKey("oauth_application.id"), nullable=False),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("granted_scopes", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("oauth_consent")
    op.drop_table("oauth_application")
