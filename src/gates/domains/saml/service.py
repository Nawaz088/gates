from __future__ import annotations

from typing import Any

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gates.config import settings as gates_settings
from gates.core.errors import NotFoundError, ValidationError
from gates.core.instance import get_instance_id
from gates.db.models.saml_connection import SamlConnection


def _build_settings(conn: SamlConnection) -> dict[str, Any]:
    return {
        "strict": True,
        "debug": gates_settings.debug,
        "sp": {
            "entityId": conn.sp_entity_id,
            "assertionConsumerService": {
                "url": conn.acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": f"{gates_settings.public_url}/v1/sso/saml/{conn.id}/slo",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": conn.idp_entity_id,
            "singleSignOnService": {
                "url": conn.idp_sso_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": conn.idp_sso_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": conn.idp_certificate,
        },
    }


async def get_connection(db: AsyncSession, connection_id: str) -> SamlConnection:
    conn = await db.get(SamlConnection, connection_id)
    if conn is None:
        raise NotFoundError(message="SAML connection not found.")
    return conn


async def list_connections(db: AsyncSession) -> list[SamlConnection]:
    instance_id = await get_instance_id(db)
    result = await db.execute(
        select(SamlConnection).where(SamlConnection.instance_id == instance_id)
    )
    return list(result.scalars().all())


async def create_connection(
    db: AsyncSession,
    name: str,
    idp_entity_id: str,
    idp_sso_url: str,
    idp_certificate: str,
    sp_entity_id: str,
    acs_url: str,
    domains: list[str] | None = None,
    attribute_mapping: dict[str, Any] | None = None,
) -> SamlConnection:
    instance_id = await get_instance_id(db)
    conn = SamlConnection(
        instance_id=instance_id,
        name=name,
        idp_entity_id=idp_entity_id,
        idp_sso_url=idp_sso_url,
        idp_certificate=idp_certificate,
        sp_entity_id=sp_entity_id,
        acs_url=acs_url,
        domains=domains or [],
        attribute_mapping=attribute_mapping or {},
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn


async def build_auth_request(
    db: AsyncSession,
    connection_id: str,
    _request_data: dict[str, Any] | None = None,
) -> str:
    conn = await get_connection(db, connection_id)
    settings_dict = _build_settings(conn)
    req = {"http_host": gates_settings.cookie_domain, "script_uri": "/"}
    auth = OneLogin_Saml2_Auth(req, settings_dict)
    return str(auth.login())


async def process_acs_response(
    db: AsyncSession,
    connection_id: str,
    _request_data: dict[str, Any] | None = None,
    _post_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn = await get_connection(db, connection_id)
    settings_dict = _build_settings(conn)
    req = {
        "http_host": gates_settings.cookie_domain,
        "script_uri": f"/v1/sso/saml/{connection_id}/acs",
    }
    auth = OneLogin_Saml2_Auth(req, settings_dict)
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        raise ValidationError(message=f"SAML response error: {', '.join(errors)}")

    if not auth.is_authenticated():
        raise ValidationError(message="SAML authentication failed.")

    attributes = auth.get_attributes()
    name_id = auth.get_nameid()

    return {
        "name_id": name_id,
        "attributes": attributes,
        "session_index": auth.get_session_index(),
    }


async def process_slo(
    db: AsyncSession,
    connection_id: str,
    _request_data: dict[str, Any] | None = None,
) -> str:
    conn = await get_connection(db, connection_id)
    settings_dict = _build_settings(conn)
    req = {"http_host": gates_settings.cookie_domain, "script_uri": ""}
    auth = OneLogin_Saml2_Auth(req, settings_dict)
    return str(auth.logout())
