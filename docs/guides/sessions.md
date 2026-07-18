# Sessions & Tokens

## How Sessions Work

Gates uses a dual-token session system:

| Token | Type | TTL | Storage |
|-------|------|-----|---------|
| **JWT** (`__session` cookie) | Signed JSON | 60 min | Client cookie |
| **Refresh** (`__session_refresh` cookie) | Opaque random | 60 days | Hashed in cache |

## JWT Claims

```json
{
  "sub": "user_cuid123",
  "sid": "session_cuid456",
  "iat": 1712345678,
  "exp": 1712349278,
  "fva": 1712345678,
  "email": "user@example.com",
  "username": "johndoe",
  "org_id": "org_cuid789",
  "org_role": "org:admin",
  "org_permissions": ["org:read", "org:write"]
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User ID |
| `sid` | Session ID |
| `iat` / `exp` | Issued at / Expiry |
| `fva` | Factor verification age (for step-up auth) |
| `email` / `username` | User identifiers |
| `org_id` / `org_role` / `org_permissions` | Active org context |

## Session Lifecycle

```
Created ──▶ Active ──▶ Expired (60 days)
               │
               ├──▶ Revoked (manual, password change)
               │
               └──▶ Ended (explicit sign-out)
```

- **Idle timeout**: 7 days of inactivity → marked `expired`
- **Absolute timeout**: 60 days from creation
- **Concurrent sessions**: Allowed (multiple devices)

## Sign In Flow

```
1. POST /v1/sign_ins  ──▶ 2. Validate credentials
                              │
                              ├── Success: issue JWT + refresh token
                              │            Set __session + __session_refresh cookies
                              │            Redirect to app
                              │
                              └── Failure: return form_password_incorrect
                                           (constant-time, no enumeration)
```

## Token Refresh

```
1. JWT expires (60 min)
2. SDK calls POST /v1/tokens (sends __session_refresh cookie)
3. Server validates refresh token, rotates it (old revoked, new issued)
4. New JWT + new refresh token set as cookies
```

## Step-Up Authentication

Endpoints requiring sensitive actions check the `fva` claim:

```python
from gates.core.auth import require_step_up

# If fva is older than 10 minutes, raises StepUpRequiredError
require_step_up(payload.get("fva"))
```

The frontend intercepts the `403 step_up_required` response and shows a re-authentication modal.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/sign_ins` | Sign in (creates session) |
| POST | `/v1/sign_outs` | Sign out (revokes session) |
| POST | `/v1/tokens` | Refresh token exchange |
| GET | `/v1/sessions` | List active sessions |
| GET | `/v1/sessions/:id` | Get session details |
| POST | `/v1/sessions/:id/revoke` | Revoke session |
| POST | `/v1/sessions/revoke_all` | Revoke all other sessions |

## Verifying JWTs (Server-Side)

```python
import jwt
from gates.config import settings

def verify_gates_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_signing_key,
        algorithms=["HS256"],
    )
```

For RS256, fetch the public key from `GET /v1/jwks`.
