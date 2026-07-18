# How Gates Works

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Your Application                    │
│  ┌──────────────────┐     ┌──────────────────────┐  │
│  │  Frontend (React)│     │  Backend (Your API)  │  │
│  │  @gates/react    │     │  verify_gates_token()│  │
│  └────────┬─────────┘     └──────────┬───────────┘  │
│           │                         │               │
│      ┌────▼─────────────────────────▼────┐          │
│      │         Gates API :8000           │          │
│      │  FastAPI + PostgreSQL + Redis     │          │
│      └───────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

## Authentication Flow

```
User                   Frontend              Gates API             Database
 │                        │                      │                    │
 │  Click Sign In         │                      │                    │
 │───────────────────────▶│                      │                    │
 │                        │  POST /v1/sign_ins   │                    │
 │                        │─────────────────────▶│                    │
 │                        │                      │  Verify password   │
 │                        │                      │───────────────────▶│
 │                        │                      │◀───────────────────│
 │                        │                      │                    │
 │                        │                      │  Create session    │
 │                        │                      │───────────────────▶│
 │                        │                      │◀───────────────────│
 │                        │                      │                    │
 │                        │  Set-Cookie:         │                    │
 │                        │  __session=(JWT)     │                    │
 │                        │  __session_refresh=  │                    │
 │                        │◀─────────────────────│                    │
 │                        │                      │                    │
 │  Redirect to /dashboard│                      │                    │
 │◀───────────────────────│                      │                    │
```

## Data Model

### Core Entities

```
instance ──┬── users ──┬── email_addresses
           │            ├── phone_numbers
           │            ├── sessions
           │            ├── passkeys
           │            ├── mfa_factors
           │            ├── backup_codes
           │            ├── external_accounts (OAuth)
           │            └── verifications
           │
           ├── organizations ──┬── memberships
           │                    ├── invitations
           │                    ├── custom_roles
           │                    └── domains
           │
           ├── api_keys
           ├── webhook_endpoints
           ├── jwt_templates
           ├── oauth_applications
           └── audit_logs
```

### Multi-Tenancy

Every entity has an `instance_id` column. A single deployment can serve multiple instances (dev/staging/prod).

## Token Strategy

| Aspect | JWT (Session) | Refresh Token |
|--------|---------------|---------------|
| Format | Signed JWT | Opaque random bytes |
| TTL | 60 minutes | 60 days |
| Storage | Browser cookie | Hashed in cache |
| Rotation | Creates new one | Old revoked on use |
| Contains | User ID, Session ID, Email, Org context | Nothing (lookup key) |

## Authentication Strategies

| Strategy | Method | MFA Compatible |
|----------|--------|----------------|
| Password | Email + password hash (Argon2id) | Yes |
| Magic Link | Single-use signed link in email | No |
| Email OTP | 6-digit code sent via email | Yes |
| SMS OTP | 6-digit code sent via SMS | Yes |
| Social OAuth | Google, GitHub, Apple, Microsoft | No |
| Passkeys | WebAuthn (biometric/platform) | No |
| SAML SSO | Enterprise SAML 2.0 IdP | No |
| OIDC SSO | Generic OpenID Connect provider | No |

## Security

- **Passwords**: Argon2id (`m=64MB, t=3, p=4`)
- **Secrets at rest**: Fernet encryption (AES-128-CBC + HMAC-SHA256)
- **Rate limiting**: Token bucket (1000 req/min per IP, configurable per endpoint)
- **Bot protection**: Turnstile / hCaptcha / reCAPTCHA
- **Headless enumeration prevention**: Constant-time sign-in responses
- **Brute-force lockout**: 5 failed attempts → 30 min lock
