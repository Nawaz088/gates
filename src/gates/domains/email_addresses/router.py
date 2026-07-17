from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.email_addresses.schemas import (
    EmailAddressCreateRequest,
    EmailAddressResponse,
    EmailAddressUpdateRequest,
)
from gates.domains.email_addresses.service import (
    add_email,
    list_user_emails,
    remove_email,
    verify_email,
)

router = APIRouter(prefix="/v1/users/{user_id}/email_addresses", tags=["email"])


@router.get("", response_model=dict)
async def api_list_emails(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    emails = await list_user_emails(db, user_id)
    return {"data": [EmailAddressResponse.model_validate(e) for e in emails]}


@router.post("", response_model=EmailAddressResponse, status_code=201)
async def api_add_email(
    user_id: str,
    body: EmailAddressCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> EmailAddressResponse:
    email = await add_email(db, user_id, body.email, verified=body.verified)
    return EmailAddressResponse.model_validate(email)


@router.post("/{email_id}/verify", response_model=EmailAddressResponse)
async def api_verify_email(
    _user_id: str,
    email_id: str,
    body: EmailAddressUpdateRequest,
    db: AsyncSession = Depends(get_session),
) -> EmailAddressResponse:
    email = await verify_email(db, email_id, body.email or "")
    return EmailAddressResponse.model_validate(email)


@router.delete("/{email_id}", status_code=204)
async def api_remove_email(
    _user_id: str,
    email_id: str,
    db: AsyncSession = Depends(get_session),
) -> None:
    await remove_email(db, email_id)
