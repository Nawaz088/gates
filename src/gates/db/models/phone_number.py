from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class PhoneNumber(Base):
    __tablename__ = "phone_number"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    default_two_factor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    linked_to: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
