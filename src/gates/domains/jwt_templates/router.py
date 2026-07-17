from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.session import get_session
from gates.domains.jwt_templates.service import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    update_template,
)

router = APIRouter(prefix="/v1/jwt_templates", tags=["jwt_templates"])


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    algorithm: str = "HS256"
    lifetime: int = 3600
    claims: dict[str, Any] = Field(default_factory=dict)
    signing_key: str | None = None


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    algorithm: str | None = None
    lifetime: int | None = None
    claims: dict[str, Any] | None = None
    signing_key: str | None = None


@router.get("")
async def api_list_templates(
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    templates = await list_templates(db)
    return {
        "data": [
            {"id": t.id, "name": t.name, "algorithm": t.algorithm,
             "lifetime": t.lifetime, "claims": t.claims}
            for t in templates
        ],
        "total_count": len(templates),
    }


@router.post("", status_code=201)
async def api_create_template(
    body: TemplateCreateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    tpl = await create_template(
        db, body.name, body.algorithm, body.lifetime, body.claims, body.signing_key,
    )
    return {"id": tpl.id, "name": tpl.name, "algorithm": tpl.algorithm, "lifetime": tpl.lifetime}


@router.get("/{template_id}")
async def api_get_template(
    template_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    tpl = await get_template(db, template_id)
    return {"id": tpl.id, "name": tpl.name, "algorithm": tpl.algorithm,
            "lifetime": tpl.lifetime, "claims": tpl.claims}


@router.patch("/{template_id}")
async def api_update_template(
    template_id: str,
    body: TemplateUpdateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    tpl = await update_template(
        db, template_id, body.name, body.algorithm, body.lifetime, body.claims, body.signing_key,
    )
    return {"id": tpl.id, "name": tpl.name, "algorithm": tpl.algorithm}


@router.delete("/{template_id}", status_code=204)
async def api_delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await delete_template(db, template_id)
