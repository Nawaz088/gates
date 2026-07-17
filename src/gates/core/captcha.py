from __future__ import annotations

from typing import Any

import httpx

from gates.config import settings


async def verify_captcha(token: str) -> dict[str, Any]:
    provider = settings.captcha_provider
    if not provider or not token:
        return {"success": False, "error": "Captcha not configured or no token provided."}

    if provider == "turnstile":
        return await _verify_turnstile(token)
    elif provider == "recaptcha":
        return await _verify_recaptcha(token)
    elif provider == "hcaptcha":
        return await _verify_hcaptcha(token)
    return {"success": False, "error": f"Unknown captcha provider: {provider}"}


async def _verify_turnstile(token: str) -> dict[str, Any]:
    secret = settings.turnstile_secret
    if not secret:
        return {"success": False, "error": "Turnstile secret not configured."}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token},
        )
        data = resp.json()
        return {"success": data.get("success", False), "error": data.get("error-codes")}


async def _verify_recaptcha(token: str) -> dict[str, Any]:
    secret = settings.turnstile_secret
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": secret, "response": token},
        )
        data = resp.json()
        return {"success": data.get("success", False), "error": data.get("error-codes")}


async def _verify_hcaptcha(token: str) -> dict[str, Any]:
    secret = settings.turnstile_secret
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://hcaptcha.com/siteverify",
            data={"secret": secret, "response": token},
        )
        data = resp.json()
        return {"success": data.get("success", False), "error": data.get("error-codes")}
