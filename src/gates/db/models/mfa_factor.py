from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class MfaFactor(Base):
    __tablename__ = "mfa_factor"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    secret_enc: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone_number_id: Mapped[str | None] = mapped_column(String(24), nullable=True)
    friendly_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
