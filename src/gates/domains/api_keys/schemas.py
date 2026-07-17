from __future__ import annotations

from datetime import datetime

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class GatesBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
        from_attributes=True,
    )


class ApiKeyCreateRequest(GatesBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    scopes: list[str] = Field(default_factory=list)


class ApiKeyCreateResponse(GatesBaseModel):
    id: str
    name: str
    description: str | None = None
    key_prefix: str
    scopes: list[str] = []
    key: str = ""
    created_at: datetime


class ApiKeyResponse(GatesBaseModel):
    id: str
    name: str
    description: str | None = None
    key_prefix: str
    scopes: list[str] = []
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime
