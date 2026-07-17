from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class EmailAddress(Base):
    __tablename__ = "email_address"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linked_to: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="email_addresses", lazy="selectin")
