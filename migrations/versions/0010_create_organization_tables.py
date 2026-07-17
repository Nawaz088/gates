"""Create organization, membership, invitation, role, domain tables.

Revision ID: 0010
Revises: 0009
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.String(1024), nullable=True),
        sa.Column("has_image", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("public_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("private_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("members_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_members", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_org_slug", "organization", ["instance_id", "slug"])

    op.create_table(
        "organization_membership",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("organization_id", sa.String(24), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("user_id", sa.String(24), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(100), nullable=False, server_default="basic_member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_membership", "organization_membership", ["organization_id", "user_id"])

    op.create_table(
        "organization_invitation",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("organization_id", sa.String(24), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("inviter_user_id", sa.String(24), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("token_hash", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invitation_email", "organization_invitation", ["email"])

    op.create_table(
        "role",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("organization_id", sa.String(24), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("permissions", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_role_key", "role", ["organization_id", "key"])

    op.create_table(
        "organization_domain",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("organization_id", sa.String(24), sa.ForeignKey("organization.id"), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enrollment_mode", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("organization_domain")
    op.drop_table("role")
    op.drop_table("organization_invitation")
    op.drop_table("organization_membership")
    op.drop_table("organization")
