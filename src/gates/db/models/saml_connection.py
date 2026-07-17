from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ARRAY, Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class SamlConnection(Base):
    __tablename__ = "saml_connection"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domains: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    idp_entity_id: Mapped[str] = mapped_column(String(1024), nullable=False)
    idp_sso_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    idp_certificate: Mapped[str] = mapped_column(String(4096), nullable=False)
    sp_entity_id: Mapped[str] = mapped_column(String(1024), nullable=False)
    acs_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    metadata_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    attribute_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
