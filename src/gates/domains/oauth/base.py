from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client


@dataclass
class OAuthUserInfo:
    provider: str
    provider_user_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    picture: str | None = None


class OAuthProvider(ABC):
    name: str = ""
    client_id: str = ""
    client_secret: str = ""
    authorize_url: str = ""
    token_url: str = ""
    userinfo_url: str = ""
    scopes: str = ""

    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=redirect_uri,
            scope=self.scopes,
        )
        url, _ = client.create_authorization_url(
            self.authorize_url,
            state=state,
        )
        return str(url)

    async def fetch_token(self, redirect_uri: str, code: str) -> dict[str, Any]:
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=redirect_uri,
        )
        token = await client.fetch_token(self.token_url, code=code)
        return dict(token)

    async def get_userinfo(self, token: dict[str, Any]) -> OAuthUserInfo:
        client = AsyncOAuth2Client(token=token)
        resp = await client.get(self.userinfo_url)
        resp.raise_for_status()
        data = resp.json()
        return self._normalize(data)

    @abstractmethod
    def _normalize(self, data: dict[str, Any]) -> OAuthUserInfo:
        ...
