# Rate Limiting

Gates uses a sliding window token bucket for rate limiting.

## Default Limits

| Endpoint | Per IP | Per Target |
|----------|--------|------------|
| `POST /v1/sign_ins` | 30/min | 5/min per email |
| `POST /v1/sign_ups` | 10/min | — |
| `POST /v1/verifications` | 20/min | 5/min per target |
| `POST /v1/oauth/*` | 60/min | — |
| `POST /v1/webhooks/*` | 10/min (admin) | — |
| **Global** | 1000/min | — |

## Rate Limit Headers

Every response includes:

```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
```

When exceeded:

```
HTTP 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
```

## Configuration

Rate limits are configurable per instance via `auth_config`:

```json
{
  "rate_limits": {
    "sign_ins": { "per_ip": 30, "per_target": 5, "window": 60 },
    "sign_ups": { "per_ip": 10, "window": 60 },
    "global": { "max_requests": 1000, "window": 60 }
  }
}
```
