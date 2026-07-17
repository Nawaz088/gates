from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class OAuthConsent(Base):
    __tablename__ = "oauth_consent"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    oauth_application_id: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[str] = mapped_column(String(24), nullable=False)
    granted_scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
