from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.auth import get_current_session
from gates.db.models.organization_domain import OrganizationDomain
from gates.db.session import get_session
from gates.domains.organizations.service import (
    accept_invitation,
    add_member,
    create_invitation,
    create_organization,
    create_role,
    delete_organization,
    get_organization,
    list_invitations,
    list_members,
    list_organizations,
    list_roles,
    remove_member,
    revoke_invitation,
    update_member_role,
    update_organization,
)

router = APIRouter(prefix="/v1/organizations", tags=["organizations"])


class OrgCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(None, max_length=100)
    public_metadata: dict[str, Any] = Field(default_factory=dict)
    private_metadata: dict[str, Any] = Field(default_factory=dict)
    max_members: int | None = None


class InviteRequest(BaseModel):
    email: str
    role: str = "basic_member"


class AcceptInviteRequest(BaseModel):
    token: str


class RoleCreateRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    permissions: list[str] = Field(default_factory=list)


class DomainAddRequest(BaseModel):
    domain: str
    enrollment_mode: str = "manual"


class DomainVerifyRequest(BaseModel):
    token: str


@router.get("")
async def api_list_orgs(
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    orgs, total = await list_organizations(db, user_id=auth["user_id"], offset=offset, limit=limit)
    return {
        "data": [
            {"id": o.id, "name": o.name, "slug": o.slug, "members_count": o.members_count,
             "created_at": str(o.created_at), "updated_at": str(o.updated_at)}
            for o in orgs
        ],
        "total_count": total,
    }


@router.post("", status_code=201)
async def api_create_org(
    body: OrgCreateRequest,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    org = await create_organization(
        db, body.name, body.slug, auth["user_id"],
        body.public_metadata, body.private_metadata, body.max_members,
    )
    return {"id": org.id, "name": org.name, "slug": org.slug, "members_count": org.members_count}


@router.get("/{org_id}")
async def api_get_org(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    org = await get_organization(db, org_id)
    return {"id": org.id, "name": org.name, "slug": org.slug, "members_count": org.members_count,
            "public_metadata": org.public_metadata, "created_at": str(org.created_at)}


@router.patch("/{org_id}")
async def api_update_org(
    org_id: str,
    body: OrgCreateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    org = await update_organization(
        db, org_id, body.name, body.slug,
        body.public_metadata, body.private_metadata, body.max_members,
    )
    return {"id": org.id, "name": org.name, "slug": org.slug}


@router.delete("/{org_id}", status_code=204)
async def api_delete_org(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await delete_organization(db, org_id)


@router.get("/{org_id}/memberships")
async def api_list_members(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    members = await list_members(db, org_id)
    return {
        "data": [
            {"id": m.id, "user_id": m.user_id, "role": m.role, "created_at": str(m.created_at)}
            for m in members
        ],
        "total_count": len(members),
    }


@router.post("/{org_id}/memberships")
async def api_add_member(
    org_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    membership = await add_member(db, org_id, body["user_id"], body.get("role", "basic_member"))
    return {"id": membership.id, "user_id": membership.user_id, "role": membership.role}


@router.patch("/{org_id}/memberships/{user_id}")
async def api_update_member_role(
    org_id: str,
    user_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    membership = await update_member_role(db, org_id, user_id, body["role"])
    return {"id": membership.id, "user_id": membership.user_id, "role": membership.role}


@router.delete("/{org_id}/memberships/{user_id}", status_code=204)
async def api_remove_member(
    org_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> None:
    await remove_member(db, org_id, user_id)


@router.get("/{org_id}/invitations")
async def api_list_invitations(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    invs = await list_invitations(db, org_id)
    return {
        "data": [
            {
                "id": i.id, "email": i.email, "role": i.role,
                "status": i.status, "created_at": str(i.created_at),
            }
            for i in invs
        ],
        "total_count": len(invs),
    }


@router.post("/{org_id}/invitations")
async def api_create_invitation(
    org_id: str,
    body: InviteRequest,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    inv = await create_invitation(db, org_id, body.email, body.role, auth["user_id"])
    return {"id": inv.id, "email": inv.email, "role": inv.role, "status": inv.status}


@router.post("/{org_id}/invitations/accept")
async def api_accept_invitation(
    org_id: str,
    body: AcceptInviteRequest,
    db: AsyncSession = Depends(get_session),
    auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    membership = await accept_invitation(db, body.token, auth["user_id"])
    return {"status": "accepted", "organization_id": org_id, "role": membership.role}


@router.post("/{org_id}/invitations/{inv_id}/revoke")
async def api_revoke_invitation(
    _org_id: str,
    inv_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    await revoke_invitation(db, inv_id)
    return {"status": "revoked"}


@router.get("/{org_id}/roles")
async def api_list_roles(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    roles = await list_roles(db, org_id)
    return {
        "data": [
            {"id": r.id, "key": r.key, "name": r.name, "permissions": r.permissions,
             "is_system": r.is_system, "description": r.description}
            for r in roles
        ],
        "total_count": len(roles),
    }


@router.post("/{org_id}/roles")
async def api_create_role(
    org_id: str,
    body: RoleCreateRequest,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    role = await create_role(db, org_id, body.key, body.name, body.permissions, body.description)
    return {"id": role.id, "key": role.key, "name": role.name, "permissions": role.permissions}


@router.get("/{org_id}/domains")
async def api_list_domains(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _auth: dict[str, Any] = Depends(get_current_session),
) -> dict[str, Any]:
    result = await db.execute(
        sa_select(OrganizationDomain).where(OrganizationDomain.organization_id == org_id)
    )
    domains = list(result.scalars().all())
    return {
        "data": [
            {"id": d.id, "domain": d.domain, "enrollment_mode": d.enrollment_mode,
             "verified_at": str(d.verified_at) if d.verified_at else None}
            for d in domains
        ],
        "total_count": len(domains),
    }
