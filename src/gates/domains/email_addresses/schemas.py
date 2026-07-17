from __future__ import annotations

from datetime import datetime

from pydantic import AliasGenerator, BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel


class EmailAddressBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
        from_attributes=True,
    )


class EmailAddressCreateRequest(EmailAddressBaseModel):
    email: EmailStr
    verified: bool = False


class EmailAddressUpdateRequest(EmailAddressBaseModel):
    email: EmailStr | None = None
    verified: bool | None = None


class EmailAddressResponse(EmailAddressBaseModel):
    id: str
    user_id: str
    email: str
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
