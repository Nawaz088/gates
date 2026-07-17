from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class Instance(Base):
    __tablename__ = "instance"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="development")
    auth_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    branding: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    users = relationship("User", back_populates="instance", lazy="selectin")
