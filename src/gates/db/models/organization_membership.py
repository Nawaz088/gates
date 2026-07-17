from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class OrganizationMembership(Base):
    __tablename__ = "organization_membership"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_membership"),
    )

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    organization_id: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="basic_member")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
