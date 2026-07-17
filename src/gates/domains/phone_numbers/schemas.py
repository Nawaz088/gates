from __future__ import annotations

from datetime import datetime

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PhoneNumberBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
        from_attributes=True,
    )


class PhoneNumberCreateRequest(PhoneNumberBaseModel):
    phone_number: str = Field(..., pattern=r"^\+[1-9]\d{6,14}$")
    verified: bool = False


class PhoneNumberUpdateRequest(PhoneNumberBaseModel):
    phone_number: str | None = Field(None, pattern=r"^\+[1-9]\d{6,14}$")
    default_two_factor: bool | None = None


class PhoneNumberResponse(PhoneNumberBaseModel):
    id: str
    user_id: str
    phone_number: str
    verified_at: datetime | None = None
    default_two_factor: bool = False
    created_at: datetime
    updated_at: datetime
