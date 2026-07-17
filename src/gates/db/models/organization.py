from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class Organization(Base):
    __tablename__ = "organization"
    __table_args__ = (
        UniqueConstraint("instance_id", "slug", name="uq_org_slug"),
    )

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    has_image: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    private_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    members_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_members: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
