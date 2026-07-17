from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class GatesBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
        from_attributes=True,
    )


class UserCreateRequest(GatesBaseModel):
    external_id: str | None = None
    username: str | None = Field(None, min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    email_address: list[str] = []
    phone_number: list[str] = []
    password: str | None = Field(None, min_length=8, max_length=128)
    public_metadata: dict[str, Any] = Field(default_factory=dict)
    private_metadata: dict[str, Any] = Field(default_factory=dict)
    unsafe_metadata: dict[str, Any] = Field(default_factory=dict)


class UserUpdateRequest(GatesBaseModel):
    external_id: str | None = None
    username: str | None = Field(None, min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    first_name: str | None = None
    last_name: str | None = None
    primary_email_id: str | None = None
    primary_phone_id: str | None = None
    public_metadata: dict[str, Any] | None = None
    private_metadata: dict[str, Any] | None = None
    unsafe_metadata: dict[str, Any] | None = None


class UserResponse(GatesBaseModel):
    id: str
    instance_id: str
    external_id: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    has_image: bool = False
    primary_email_id: str | None = None
    primary_phone_id: str | None = None
    two_factor_enabled: bool = False
    banned: bool = False
    public_metadata: dict[str, Any] = Field(default_factory=dict)
    unsafe_metadata: dict[str, Any] = Field(default_factory=dict)
    last_sign_in_at: datetime | None = None
    last_active_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class EmailAddressResponse(GatesBaseModel):
    id: str
    user_id: str
    email: str
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
