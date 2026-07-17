from __future__ import annotations

from datetime import datetime

from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class GatesBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
        from_attributes=True,
    )


class SessionResponse(GatesBaseModel):
    id: str
    user_id: str
    client_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    status: str = "active"
    active_org_id: str | None = None
    last_active_at: datetime
    expire_at: datetime
    created_at: datetime


class SessionListResponse(GatesBaseModel):
    data: list[SessionResponse]
    total_count: int


class SessionTokensResponse(GatesBaseModel):
    jwt: str
    refresh_token: str
