"""Create saml_connection and oidc_connection tables.

Revision ID: 0011
Revises: 0010
Create Date: 2025-07-18
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saml_connection",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domains", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("idp_entity_id", sa.String(1024), nullable=False),
        sa.Column("idp_sso_url", sa.String(1024), nullable=False),
        sa.Column("idp_certificate", sa.String(4096), nullable=False),
        sa.Column("sp_entity_id", sa.String(1024), nullable=False),
        sa.Column("acs_url", sa.String(1024), nullable=False),
        sa.Column("metadata_url", sa.String(1024), nullable=True),
        sa.Column("attribute_mapping", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "oidc_connection",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("instance_id", sa.String(24), sa.ForeignKey("instance.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(1024), nullable=False),
        sa.Column("client_id", sa.String(1024), nullable=False),
        sa.Column("client_secret_enc", sa.String(512), nullable=False),
        sa.Column("discovery_url", sa.String(1024), nullable=True),
        sa.Column("scopes", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("domains", sa.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("attribute_mapping", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oidc_connection")
    op.drop_table("saml_connection")
