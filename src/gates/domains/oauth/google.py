from __future__ import annotations

from typing import Any

from gates.domains.oauth.base import OAuthProvider, OAuthUserInfo


class GoogleProvider(OAuthProvider):
    name = "google"
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    scopes = "openid email profile"

    def _normalize(self, data: dict[str, Any]) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=data["sub"],
            email=data.get("email"),
            first_name=data.get("given_name"),
            last_name=data.get("family_name"),
            picture=data.get("picture"),
        )
