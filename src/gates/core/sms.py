from __future__ import annotations

import logging
from typing import Any

from gates.config import settings

log = logging.getLogger("gates.sms")


async def send_sms(to: str, body: str) -> dict[str, Any]:
    if settings.twilio_account_sid and settings.twilio_auth_token:
        return await _send_twilio(to, body)
    log.info("SMS stub: to=%s body=%s", to, body[:100])
    return {"status": "logged", "provider": "stub"}


async def _send_twilio(to: str, body: str) -> dict[str, Any]:
    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    message = client.messages.create(
        to=to,
        from_=settings.twilio_messaging_service_sid,
        body=body,
    )
    return {"status": "sent", "sid": message.sid}
