from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.phone_numbers.schemas import (
    PhoneNumberCreateRequest,
    PhoneNumberResponse,
    PhoneNumberUpdateRequest,
)
from gates.domains.phone_numbers.service import (
    add_phone,
    list_user_phones,
    remove_phone,
    set_default_two_factor,
    verify_phone,
)

router = APIRouter(prefix="/v1/users/{user_id}/phone_numbers", tags=["phone"])


class VerifyCodeRequest(BaseModel):
    code: str


@router.get("")
async def api_list_phones(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    phones = await list_user_phones(db, user_id)
    return {
        "data": [PhoneNumberResponse.model_validate(p).model_dump() for p in phones],
        "total_count": len(phones),
    }


@router.post("", status_code=201)
async def api_add_phone(
    user_id: str,
    body: PhoneNumberCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    phone = await add_phone(db, user_id, body.phone_number, verified=body.verified)
    return PhoneNumberResponse.model_validate(phone).model_dump()


@router.post("/{phone_id}/verify")
async def api_verify_phone(
    _user_id: str,
    phone_id: str,
    body: VerifyCodeRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    phone = await verify_phone(db, phone_id, body.code)
    return PhoneNumberResponse.model_validate(phone).model_dump()


@router.patch("/{phone_id}")
async def api_update_phone(
    user_id: str,
    phone_id: str,
    body: PhoneNumberUpdateRequest,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if body.default_two_factor:
        phone = await set_default_two_factor(db, user_id, phone_id)
        return PhoneNumberResponse.model_validate(phone).model_dump()
    raise NotImplementedError


@router.delete("/{phone_id}", status_code=204)
async def api_remove_phone(
    _user_id: str,
    phone_id: str,
    db: AsyncSession = Depends(get_session),
) -> None:
    await remove_phone(db, phone_id)
