from __future__ import annotations

from typing import Any

from gates.domains.oauth.base import OAuthProvider, OAuthUserInfo


class GitHubProvider(OAuthProvider):
    name = "github"
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    userinfo_url = "https://api.github.com/user"
    scopes = "user:email"

    def _normalize(self, data: dict[str, Any]) -> OAuthUserInfo:
        name = (data.get("name") or "").strip()
        first = last = None
        if name and " " in name:
            parts = name.split(" ", 1)
            first, last = parts[0], parts[1]
        elif name:
            first = name
        return OAuthUserInfo(
            provider=self.name,
            provider_user_id=str(data["id"]),
            email=data.get("email"),
            first_name=first,
            last_name=last,
            picture=data.get("avatar_url"),
        )
