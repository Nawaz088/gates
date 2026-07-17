from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from gates.db.session import get_session
from gates.domains.users.schemas import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from gates.domains.users.service import (
    ban_user,
    create_user,
    delete_user,
    get_user,
    list_users,
    lock_user,
    unban_user,
    unlock_user,
    update_user,
)

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("", response_model=dict)
async def api_list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    users, total = await list_users(db, offset=offset, limit=limit)
    return {
        "data": [UserResponse.model_validate(u) for u in users],
        "total_count": total,
    }


@router.post("", response_model=UserResponse, status_code=201)
async def api_create_user(
    body: UserCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    email = body.email_address[0] if body.email_address else None
    user = await create_user(
        db,
        email=email,
        password=body.password,
        username=body.username,
        first_name=body.first_name,
        last_name=body.last_name,
        public_metadata=body.public_metadata,
        private_metadata=body.private_metadata,
        unsafe_metadata=body.unsafe_metadata,
        external_id=body.external_id,
    )
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def api_get_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    user = await get_user(db, user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def api_update_user(
    user_id: str,
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    kwargs = body.model_dump(exclude_unset=True, mode="python")
    user = await update_user(db, user_id, **kwargs)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def api_delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> None:
    await delete_user(db, user_id)


@router.post("/{user_id}/ban", response_model=UserResponse)
async def api_ban_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    user = await ban_user(db, user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/unban", response_model=UserResponse)
async def api_unban_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    user = await unban_user(db, user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/lock", response_model=UserResponse)
async def api_lock_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    user = await lock_user(db, user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/unlock", response_model=UserResponse)
async def api_unlock_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    user = await unlock_user(db, user_id)
    return UserResponse.model_validate(user)
