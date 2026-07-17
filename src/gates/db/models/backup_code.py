from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class BackupCode(Base):
    __tablename__ = "backup_code"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    mfa_factor_id: Mapped[str] = mapped_column(String(24), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
