from __future__ import annotations

from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.core.crypto import decrypt
from gates.core.errors import NotFoundError
from gates.core.instance import get_instance_id
from gates.db.models.oidc_connection import OIDCConnection


async def get_connection(db: AsyncSession, connection_id: str) -> OIDCConnection:
    conn = await db.get(OIDCConnection, connection_id)
    if conn is None:
        raise NotFoundError(message="OIDC connection not found.")
    return conn


async def list_connections(db: AsyncSession) -> list[OIDCConnection]:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(OIDCConnection).where(OIDCConnection.instance_id == instance_id)
    )
    return list(result.scalars().all())


async def create_connection(
    db: AsyncSession,
    name: str,
    issuer: str,
    client_id: str,
    client_secret: str,
    discovery_url: str | None = None,
    scopes: list[str] | None = None,
    domains: list[str] | None = None,
    attribute_mapping: dict[str, Any] | None = None,
) -> OIDCConnection:
    instance_id = await get_instance_id(db)
    from gates.core.crypto import encrypt

    conn = OIDCConnection(
        instance_id=instance_id,
        name=name,
        issuer=issuer,
        client_id=client_id,
        client_secret_enc=encrypt(client_secret),
        discovery_url=discovery_url,
        scopes=scopes or ["openid", "email", "profile"],
        domains=domains or [],
        attribute_mapping=attribute_mapping or {},
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn


def get_authorize_url(
    conn: OIDCConnection,
    redirect_uri: str,
    state: str,
) -> str:
    client_secret = decrypt(conn.client_secret_enc)
    client = AsyncOAuth2Client(
        client_id=conn.client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=" ".join(conn.scopes),
    )
    url, _ = client.create_authorization_url(
        conn.issuer,
        state=state,
    )
    return str(url)


async def process_callback(
    conn: OIDCConnection,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    client_secret = decrypt(conn.client_secret_enc)
    client = AsyncOAuth2Client(
        client_id=conn.client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )
    await client.fetch_token(conn.issuer, code=code)
    userinfo = await client.get(conn.issuer)
    userinfo.raise_for_status()
    data = userinfo.json()
    return {
        "sub": data.get("sub"),
        "email": data.get("email"),
        "name": data.get("name"),
        "preferred_username": data.get("preferred_username"),
    }
