from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    has_image: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primary_email_id: Mapped[str | None] = mapped_column(String(24), nullable=True)
    primary_phone_id: Mapped[str | None] = mapped_column(String(24), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # argon2id
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    private_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    unsafe_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    last_sign_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    email_addresses = relationship("EmailAddress", back_populates="user", lazy="selectin")
    instance = relationship("Instance", back_populates="users", lazy="selectin")
