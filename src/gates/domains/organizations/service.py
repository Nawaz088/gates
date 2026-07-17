from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Any

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.clock import now
from gates.core.errors import ConflictError, NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.core.security import random_token_str
from gates.db.models.organization import Organization
from gates.db.models.organization_domain import OrganizationDomain
from gates.db.models.organization_invitation import OrganizationInvitation
from gates.db.models.organization_membership import OrganizationMembership
from gates.db.models.role import Role

MAX_SLUG_LENGTH = 100


async def create_organization(
    db: AsyncSession,
    name: str,
    slug: str | None = None,
    created_by_user_id: str | None = None,
    public_metadata: dict[str, Any] | None = None,
    private_metadata: dict[str, Any] | None = None,
    max_members: int | None = None,
) -> Organization:
    instance_id = await get_instance_id(db)

    org_slug = slug or name.lower().replace(" ", "-")[:MAX_SLUG_LENGTH]

    existing = await db.execute(
        select(Organization).where(
            Organization.instance_id == instance_id,
            Organization.slug == org_slug,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message=f"Organization with slug '{org_slug}' already exists.")

    org = Organization(
        instance_id=instance_id,
        name=name,
        slug=org_slug,
        public_metadata=public_metadata or {},
        private_metadata=private_metadata or {},
        max_members=max_members,
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)

    if created_by_user_id:
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=created_by_user_id,
            role="org:admin",
        )
        db.add(membership)
        org.members_count = 1

    await db.commit()
    await db.refresh(org)
    return org


async def get_organization(db: AsyncSession, org_id: str) -> Organization:
    org = await db.get(Organization, org_id)
    if org is None:
        raise NotFoundError(message="Organization not found.")
    return org


async def list_organizations(
    db: AsyncSession,
    user_id: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Organization], int]:
    query = select(Organization)

    if user_id:
        subq = select(OrganizationMembership.organization_id).where(
            OrganizationMembership.user_id == user_id
        )
        query = query.where(Organization.id.in_(subq))

    total_q = select(sa_func.count()).select_from(query.subquery())
    total = await db.scalar(total_q) or 0

    query = query.order_by(Organization.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    orgs = list(result.scalars().all())
    return orgs, total


async def update_organization(
    db: AsyncSession,
    org_id: str,
    name: str | None = None,
    slug: str | None = None,
    public_metadata: dict[str, Any] | None = None,
    private_metadata: dict[str, Any] | None = None,
    max_members: int | None = None,
) -> Organization:
    org = await get_organization(db, org_id)
    if name is not None:
        org.name = name
    if slug is not None:
        org.slug = slug
    if public_metadata is not None:
        org.public_metadata = public_metadata
    if private_metadata is not None:
        org.private_metadata = private_metadata
    if max_members is not None:
        org.max_members = max_members
    await db.commit()
    await db.refresh(org)
    return org


async def delete_organization(db: AsyncSession, org_id: str) -> None:
    org = await get_organization(db, org_id)
    await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id
        )
    )
    await db.delete(org)
    await db.commit()


async def add_member(
    db: AsyncSession,
    org_id: str,
    user_id: str,
    role: str = "basic_member",
) -> OrganizationMembership:
    existing = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message="User is already a member of this organization.")

    org = await get_organization(db, org_id)
    if org.max_members and org.members_count >= org.max_members:
        raise ValidationError(message="Organization has reached the maximum number of members.")

    membership = OrganizationMembership(
        organization_id=org_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    org.members_count = (org.members_count or 0) + 1
    await db.commit()
    await db.refresh(membership)
    return membership


async def update_member_role(
    db: AsyncSession,
    org_id: str,
    user_id: str,
    role: str,
) -> OrganizationMembership:
    result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise NotFoundError(message="Membership not found.")
    membership.role = role
    await db.commit()
    await db.refresh(membership)
    return membership


async def remove_member(db: AsyncSession, org_id: str, user_id: str) -> None:
    result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise NotFoundError(message="Membership not found.")
    await db.delete(membership)
    org = await get_organization(db, org_id)
    org.members_count = max(0, (org.members_count or 1) - 1)
    await db.commit()


async def list_members(
    db: AsyncSession,
    org_id: str,
) -> list[OrganizationMembership]:
    result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id
        )
    )
    return list(result.scalars().all())


async def create_invitation(
    db: AsyncSession,
    org_id: str,
    email: str,
    role: str = "basic_member",
    inviter_user_id: str | None = None,
) -> OrganizationInvitation:
    instance_id = await get_instance_id(db)

    existing = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message="A pending invitation already exists for this email.")

    raw_token = random_token_str(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    invitation = OrganizationInvitation(
        organization_id=org_id,
        instance_id=instance_id,
        email=email,
        role=role,
        inviter_user_id=inviter_user_id or "",
        token_hash=token_hash,
        expires_at=now() + timedelta(days=30),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation


async def accept_invitation(
    db: AsyncSession,
    token: str,
    user_id: str,
) -> OrganizationMembership:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.token_hash == token_hash,
            OrganizationInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise ValidationError(message="Invalid or expired invitation token.")

    if invitation.expires_at < now():
        invitation.status = "auto_revoked"
        await db.commit()
        raise ValidationError(message="Invitation has expired.")

    membership = await add_member(db, invitation.organization_id, user_id, role=invitation.role)
    invitation.status = "accepted"
    await db.commit()
    return membership


async def revoke_invitation(db: AsyncSession, inv_id: str) -> None:
    inv = await db.get(OrganizationInvitation, inv_id)
    if inv is None:
        raise NotFoundError(message="Invitation not found.")
    inv.status = "revoked"
    await db.commit()


async def list_invitations(
    db: AsyncSession,
    org_id: str,
    status: str | None = None,
) -> list[OrganizationInvitation]:
    query = select(OrganizationInvitation).where(
        OrganizationInvitation.organization_id == org_id
    )
    if status:
        query = query.where(OrganizationInvitation.status == status)
    query = query.order_by(OrganizationInvitation.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_role(
    db: AsyncSession,
    org_id: str,
    key: str,
    name: str,
    permissions: list[str],
    description: str | None = None,
) -> Role:
    existing = await db.execute(
        select(Role).where(
            Role.organization_id == org_id,
            Role.key == key,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message=f"Role with key '{key}' already exists.")

    role = Role(
        organization_id=org_id,
        key=key,
        name=name,
        description=description,
        permissions=permissions,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def list_roles(db: AsyncSession, org_id: str) -> list[Role]:
    result = await db.execute(
        select(Role).where(Role.organization_id == org_id)
    )
    return list(result.scalars().all())


async def add_domain(
    db: AsyncSession,
    org_id: str,
    domain: str,
    enrollment_mode: str = "manual",
) -> OrganizationDomain:
    existing = await db.execute(
        select(OrganizationDomain).where(OrganizationDomain.domain == domain)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(message="Domain is already associated with an organization.")

    token = random_token_str(32)
    org_domain = OrganizationDomain(
        organization_id=org_id,
        domain=domain,
        verification_token=token,
        enrollment_mode=enrollment_mode,
    )
    db.add(org_domain)
    await db.commit()
    await db.refresh(org_domain)
    return org_domain


async def verify_domain(db: AsyncSession, domain_id: str, token: str) -> OrganizationDomain:
    org_domain = await db.get(OrganizationDomain, domain_id)
    if org_domain is None:
        raise NotFoundError(message="Domain not found.")
    if org_domain.verification_token != token:
        raise ValidationError(message="Invalid verification token.")
    org_domain.verified_at = now()
    org_domain.verification_token = None
    await db.commit()
    await db.refresh(org_domain)
    return org_domain
