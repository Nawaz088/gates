from __future__ import annotations

from typing import Any

from gates.domains.oauth.base import OAuthProvider, OAuthUserInfo


class AppleProvider(OAuthProvider):
    name = "apple"
    authorize_url = "https://appleid.apple.com/auth/authorize"
    token_url = "https://appleid.apple.com/auth/token"
    userinfo_url = ""
    scopes = "name email"

    async def get_userinfo(self, token: dict[str, Any]) -> OAuthUserInfo:
        id_token = token.get("id_token", "")
        if not id_token:
            return OAuthUserInfo(
                provider=self.name,
                provider_user_id=token.get("sub", ""),
                email=token.get("email"),
            )
        import jwt
        claims = jwt.decode(id_token, options={"verify_signature": False})
        email = claims.get("email") or token.get("email")
        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=claims.get("sub", ""),
            email=email,
            first_name=claims.get("given_name"),
            last_name=claims.get("family_name"),
        )

    def _normalize(self, data: dict[str, Any]) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=data.get("sub", ""),
            email=data.get("email"),
        )
