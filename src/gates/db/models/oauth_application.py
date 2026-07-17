from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from gates.core.utils import generate_cuid2
from gates.db.base import Base


class OAuthApplication(Base):
    __tablename__ = "oauth_application"

    id: Mapped[str] = mapped_column(String(24), primary_key=True, default=generate_cuid2)
    instance_id: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    client_secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    redirect_uris: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    homepage_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
