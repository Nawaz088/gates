from __future__ import annotations

from typing import Any

from gates.domains.oauth.base import OAuthProvider, OAuthUserInfo


class MicrosoftProvider(OAuthProvider):
    name = "microsoft"
    authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    userinfo_url = "https://graph.microsoft.com/v1.0/me"
    scopes = "User.Read openid email profile"

    def _normalize(self, data: dict[str, Any]) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=data.get("id", ""),
            email=data.get("mail") or data.get("userPrincipalName"),
            first_name=data.get("givenName"),
            last_name=data.get("surname"),
            picture=None,
        )
