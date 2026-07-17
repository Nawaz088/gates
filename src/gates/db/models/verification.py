from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class Verification(Base):
    __tablename__ = "verification"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(24), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "extra_data", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
