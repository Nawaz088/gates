from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    active_org_id: Mapped[str | None] = mapped_column(String(24), nullable=True)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expire_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def is_expired(self) -> bool:
        return self.expire_at < datetime.now(UTC)

    @property
    def is_idle(self) -> bool:
        idle_cutoff = datetime.now(UTC) - timedelta(days=7)
        return self.last_active_at < idle_cutoff

    @property
    def is_valid(self) -> bool:
        return self.status == "active" and not self.is_expired
