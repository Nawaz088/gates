# Webhooks

Gates can send outgoing webhooks to your application when events occur.

## Available Events

```
user.created           session.created        organization.created
user.updated           session.revoked        organization.updated
user.deleted           session.ended          organization.deleted
user.banned                                    organizationMembership.created
user.unbanned                                  organizationMembership.updated
email.created                                  organizationMembership.deleted
email.verified         passkey.created         organizationInvitation.created
email.deleted          passkey.deleted         organizationInvitation.accepted
phone.created                                  organizationInvitation.revoked
phone.verified         mfaFactor.enabled
phone.deleted          mfaFactor.disabled     apiKey.created
                                              apiKey.deleted
```

## Setting Up an Endpoint

```bash
curl -X POST http://localhost:8000/v1/webhooks/endpoints \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/gates",
    "events": ["user.created", "user.updated", "user.deleted"],
    "enabled": true
  }'
```

Response includes the signing secret:

```json
{
  "id": "endpoint_cuid123",
  "url": "https://your-app.com/webhooks/gates",
  "events": ["user.created", "user.updated", "user.deleted"],
  "secret": "whsec_abc123def456..."
}
```

## Verifying Webhook Signatures

Every webhook request includes a `Gates-Signature` header:

```
Gates-Signature: t=1712345678,v1=abc123def456...
```

```python
import hmac
import hashlib
import time

def verify_gates_webhook(payload: bytes, signature_header: str, secret: str) -> bool:
    parts = signature_header.split(",")
    if len(parts) < 2:
        return False
    timestamp = int(parts[0][2:])  # t=1712345678
    sig = parts[1][3:]             # v1=<hex>

    # Replay protection: reject if older than 5 minutes
    if abs(time.time() - timestamp) > 300:
        return False

    data = str(timestamp).encode() + b"." + payload
    expected = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)
```

```javascript
// Node.js
const crypto = require("crypto");

function verifyGatesWebhook(payload, signatureHeader, secret) {
  const parts = signatureHeader.split(",");
  if (parts.length < 2) return false;
  const timestamp = parseInt(parts[0].slice(2));
  const sig = parts[1].slice(3);

  if (Math.abs(Date.now() / 1000 - timestamp) > 300) return false;

  const data = `${timestamp}.${payload}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(data)
    .digest("hex");

  return crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
}
```

## Retry Mechanism

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 30 seconds |
| 3 | 5 minutes |
| 4 | 30 minutes |
| 5 | 2 hours |
| 6 | 8 hours |

After 6 failed attempts, the delivery is marked as `failed`.

## Manual Redelivery

```bash
curl -X POST http://localhost:8000/v1/webhooks/endpoints/:id/deliveries/:delivery_id/redeliver \
  -H "Authorization: Bearer <token>"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/webhooks/endpoints` | List endpoints |
| POST | `/v1/webhooks/endpoints` | Create endpoint |
| GET | `/v1/webhooks/endpoints/:id` | Get endpoint |
| PATCH | `/v1/webhooks/endpoints/:id` | Update endpoint |
| DELETE | `/v1/webhooks/endpoints/:id` | Delete endpoint |
| GET | `/v1/webhooks/endpoints/:id/deliveries` | List deliveries |
| POST | `/v1/webhooks/endpoints/:id/deliveries/:id/redeliver` | Retry delivery |
| GET | `/v1/webhooks/endpoints/events` | List available events |
