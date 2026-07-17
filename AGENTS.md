# AGENTS.md — `gates` Authentication Platform

> **Mission:** Build `gates`, a self-hostable, full-featured authentication and user-management platform that is feature-equivalent to [Clerk](https://clerk.com). Any agent reading this document must be able to pick up the codebase, understand the architecture, and implement a feature without further clarification.

---

## 0. How to use this document

- **You are an agent working on `gates`.** Read this file fully before touching code.
- Every feature below is in scope unless explicitly marked `OUT OF SCOPE (v1)`.
- All code MUST follow the conventions in §3.
- If a requirement is ambiguous, pick the option that mirrors Clerk's behavior and document the choice in a `DECISIONS.md` entry.
- Never silently skip a requirement. If a sub-task is blocked, mark it `// TODO(gates): <reason>` and surface it to the user.

---

## 1. Tech stack (locked)

| Layer            | Choice                                                      |
| ---------------- | ----------------------------------------------------------- |
| Backend          | **Python 3.12**, **FastAPI**, **Pydantic v2**               |
| ORM / DB driver  | **SQLAlchemy 2.x (async)**, `asyncpg`                       |
| Database         | **PostgreSQL 16**                                           |
| Migrations       | **Alembic**                                                 |
| Cache / queue    | **Redis 7** (rate limit, sessions, job queue)              |
| Task queue       | **ARQ** (async Redis-based)                                 |
| Email            | **Postmark** (primary) + **SES** (fallback)                 |
| SMS              | **Twilio**                                                  |
| Object storage   | **S3-compatible** (avatars, attachments)                   |
| OAuth            | `authlib`                                                   |
| Password hashing | **Argon2id** (`argon2-cffi`)                                |
| TOTP             | `pyotp`                                                     |
| WebAuthn         | `py_webauthn`                                               |
| SAML             | `python3-saml`                                              |
| OIDC             | `authlib`                                                   |
| Crypto / tokens  | `cryptography`, `PyJWT`                                     |
| Frontend (UI)    | **React 18 + TypeScript + Vite**                            |
| Frontend (frame) | Drop-in components for **Next.js, React (Vite), Remix**     |
| Styling          | **Tailwind CSS** + **Radix UI** primitives                  |
| Testing          | `pytest`, `pytest-asyncio`, `httpx`, `playwright` (E2E)     |
| Lint / format    | `ruff`, `mypy --strict`, `prettier`, `eslint`               |
| Containerization | `docker compose` for dev; multi-stage `Dockerfile` for prod |

**Package manager:** `uv` (Python), `pnpm` (frontend).

---

## 2. Repository layout

```
gates/
├── AGENTS.md                       # this file
├── README.md
├── DECISIONS.md                    # architecture decision log
├── pyproject.toml
├── uv.lock
├── docker-compose.yml              # postgres, redis, mailhog, minio
├── .env.example
├── alembic.ini
├── migrations/                     # alembic
│   └── versions/
├── src/
│   └── gates/
│       ├── main.py                 # FastAPI app factory
│       ├── config.py               # pydantic-settings
│       ├── db/
│       │   ├── base.py             # DeclarativeBase
│       │   ├── session.py          # async engine + sessionmaker
│       │   └── models/             # SQLAlchemy ORM models
│       ├── core/                   # cross-cutting concerns
│       │   ├── security.py         # argon2, jwt, random tokens
│       │   ├── crypto.py           # at-rest encryption (Fernet)
│       │   ├── ratelimit.py        # token bucket via Redis
│       │   ├── audit.py            # audit log helper
│       │   ├── errors.py           # standard exception types
│       │   └── clock.py            # injectable now() for tests
│       ├── domains/
│       │   ├── users/
│       │   │   ├── models.py
│       │   │   ├── schemas.py
│       │   │   ├── service.py
│       │   │   ├── router.py
│       │   │   └── tests/
│       │   ├── sessions/
│       │   ├── passwords/
│       │   ├── email_addresses/
│       │   ├── phone_numbers/
│       │   ├── oauth/              # social + OIDC providers
│       │   │   ├── google.py
│       │   │   ├── github.py
│       │   │   ├── apple.py
│       │   │   ├── microsoft.py
│       │   │   └── base.py
│       │   ├── saml/
│       │   ├── passkeys/           # WebAuthn
│       │   ├── mfa/                # TOTP, SMS, backup codes
│       │   ├── magic_links/
│       │   ├── otp/                # email/sms one-time codes
│       │   ├── verifications/
│       │   ├── organizations/
│       │   ├── roles/
│       │   ├── invitations/
│       │   ├── webhooks/
│       │   ├── api_keys/
│       │   ├── jwt_templates/
│       │   ├── impersonation/
│       │   ├── audit_logs/
│       │   ├── billing/            # OUT OF SCOPE v1 (see §14)
│       │   └── instance/           # tenant config (dev/stg/prod instances)
│       ├── api/
│       │   ├── v1/                 # /v1/* — public REST API (mirrors Clerk)
│       │   └── internal/           # /internal/* — SDK-to-backend
│       ├── webhooks/               # outgoing webhook dispatch
│       ├── jobs/                   # ARQ workers
│       ├── templates/              # email/sms templates (jinja2)
│       └── utils/
├── sdks/
│   ├── react/                      # @gates/react — hooks + components
│   ├── nextjs/                     # @gates/nextjs — App Router wrappers
│   ├── remix/                      # @gates/remix
│   ├── server-python/              # @gates/server-python (FastAPI helper)
│   └── server-node/                # @gates/server-node (Express helper)
├── apps/
│   └── dashboard/                  # tenant admin UI (Clerk Dashboard clone)
│       ├── package.json
│       ├── vite.config.ts
│       └── src/
└── e2e/                            # playwright tests
```

Each domain folder follows the same pattern: `models.py`, `schemas.py`, `service.py`, `router.py`, `tests/`. **No business logic in routers — routers only translate HTTP ↔ service.**

---

## 3. Coding conventions (mandatory)

### Python
- Python 3.12, full type hints, `mypy --strict` clean.
- Async everywhere (no blocking I/O in request handlers).
- All public functions and services take an `AsyncSession` as the first arg after `self` (no module-level session globals).
- Use `pydantic` models at the API boundary; SQLAlchemy models never leave the service layer.
- Errors raised as `core.errors.GatesError` subclasses with `code`, `http_status`, `message`, `details`. Map to HTTP via a single exception handler.
- IDs: **cuid2** (24 chars) for user-facing entities, **UUIDv7** for internal join rows.
- Timestamps: `TIMESTAMPTZ` in DB, `datetime` in Python (UTC, `tzinfo=UTC`).
- Money/numeric: `Numeric(precision, scale)`. Never `float` for money.
- Secrets at rest: encrypted with Fernet; key from `GATES_FIELD_ENCRYPTION_KEY` env. See §11.
- No print, no `Any`, no `# type: ignore` without an inline justification.
- Tests: `pytest` with `httpx.AsyncClient` against a transactional Postgres test DB. 90% line coverage target on `service.py` files.

### Frontend (TypeScript)
- Strict TS, no `any`, no non-null `!` outside tests.
- Components are pure, presentational, controlled via props or context. State lives in hooks.
- Styling: Tailwind utility classes only. No CSS modules, no styled-components.
- All SDK exports are tree-shakable. Default export forbidden.
- Component package names: `@gates/react`, `@gates/nextjs`, `@gates/remix`.

### Git / PR
- Commit format: `feat(scope): ...`, `fix(scope): ...`, `chore(scope): ...`, `docs: ...`, `test(scope): ...`.
- One feature per PR. PR description must link the AGENTS.md section it implements.

---

## 4. Core domain model (must exist)

The following entities mirror Clerk's data model. Each is its own SQLAlchemy model in `src/gates/db/models/`. Field names use `snake_case` in DB and Pydantic, but the **public REST API uses Clerk's camelCase** (e.g. `firstName`, `lastName`) — provide a Pydantic alias generator.

### 4.1 `instance`
Tenant config. Multiple instances per deployment (dev / staging / prod). Mirrors Clerk's instance concept.
- `id` (cuid2)
- `name` (string)
- `environment` enum(`development`, `staging`, `production`)
- `auth_config` (JSONB) — enabled strategies, MFA policy, password policy
- `branding` (JSONB) — logo, colors, hosted pages config
- `created_at`, `updated_at`

### 4.2 `user`
- `id`, `instance_id` (FK)
- `external_id` (string, optional — your app's user id, unique per instance)
- `username` (string, unique per instance, nullable)
- `first_name`, `last_name` (string, nullable)
- `image_url` (string, nullable — S3 URL)
- `has_image` (bool)
- `primary_email_id`, `primary_phone_id` (FK nullable, set after creation)
- `password_hash` (string, nullable — argon2id)
- `two_factor_enabled` (bool, default false)
- `banned` (bool, default false)
- `ban_reason` (string, nullable)
- `locked_at`, `locked_until` (timestamp, nullable — brute-force lock)
- `public_metadata` (JSONB, default `{}`) — readable by the user, no secrets
- `private_metadata` (JSONB, default `{}`) — readable by the user, can hold PII
- `unsafe_metadata` (JSONB, default `{}`) — writable by the user from the client
- `last_sign_in_at`, `last_active_at` (timestamp, nullable)
- `failed_attempts` (int, default 0)
- `created_at`, `updated_at`

### 4.3 `email_address`
- `id`, `user_id` (FK), `instance_id`
- `email` (citext, unique per instance)
- `verification_token` (string, nullable)
- `verification_token_expires_at`
- `verified_at` (timestamp, nullable)
- `linked_to` (other email address id, nullable — for account linking)

### 4.4 `phone_number`
- `id`, `user_id` (FK), `instance_id`
- `phone_number` (string, E.164)
- `verified_at` (timestamp, nullable)
- `default_two_factor` (bool) — used for SMS MFA default
- `linked_to` (FK nullable)

### 4.5 `external_account` (social / SAML / OIDC connections)
- `id`, `user_id` (FK), `instance_id`
- `provider` enum(`google`, `github`, `apple`, `microsoft`, `saml_<custom>`, `oidc_<custom>`)
- `provider_user_id` (string)
- `email` (string, nullable)
- `scopes` (string array)
- `access_token_enc`, `refresh_token_enc` (encrypted, nullable)
- `id_token_enc` (encrypted, nullable)
- `token_expires_at` (timestamp, nullable)
- `passwordless` (bool) — true if user signed up via this provider only
- Unique `(instance_id, provider, provider_user_id)`.

### 4.6 `session`
- `id`, `user_id` (FK), `instance_id`
- `client_id` (string — browser/device fingerprint hash)
- `ip_address` (inet), `user_agent` (string)
- `status` enum(`active`, `revoked`, `expired`, `ended`)
- `last_active_at`, `expire_at` (default = now + 60 days for refresh)
- `created_at`
- Index on `(user_id, status, last_active_at)`.

### 4.7 `passkey` (WebAuthn)
- `id`, `user_id` (FK)
- `credential_id` (bytea, unique)
- `public_key` (bytea)
- `sign_count` (uint32)
- `transports` (string array)
- `aaguid` (uuid, nullable)
- `backup_eligible`, `backup_state` (bool)
- `name` (string — user-friendly label)
- `last_used_at` (timestamp, nullable)

### 4.8 `mfa_factor`
- `id`, `user_id` (FK), `instance_id`
- `type` enum(`totp`, `sms`, `backup_code`, `phone_code`)
- `status` enum(`verified`, `unverified`)
- `secret_enc` (encrypted — for TOTP seed)
- `phone_number_id` (FK, nullable — for SMS factor)
- `friendly_name` (string)
- `created_at`, `updated_at`

### 4.9 `backup_code`
- `id`, `user_id` (FK), `mfa_factor_id` (FK)
- `code_hash` (string — argon2id)
- `used_at` (timestamp, nullable)
- 10 codes generated on TOTP enroll; user can regenerate.

### 4.10 `organization`
- `id`, `instance_id`
- `name` (string)
- `slug` (string, unique per instance, regex `^[a-z0-9-]+$`)
- `logo_url` (string, nullable)
- `has_image` (bool)
- `public_metadata`, `private_metadata` (JSONB)
- `members_count` (int, denormalized, maintained by trigger/service)
- `max_members` (int, nullable — plan limit)
- `created_at`, `updated_at`

### 4.11 `organization_membership`
- `id`, `organization_id` (FK), `user_id` (FK)
- `role` (string — FK to `role.key`, default `basic_member`)
- `created_at`
- Unique `(organization_id, user_id)`.

### 4.12 `organization_invitation`
- `id`, `organization_id` (FK), `instance_id`
- `email` (citext)
- `role` (string)
- `inviter_user_id` (FK)
- `status` enum(`pending`, `accepted`, `revoked`, `auto_revoked`)
- `token_hash` (string)
- `expires_at` (created + 30 days)
- `created_at`, `updated_at`

### 4.13 `role` (custom roles per org)
- `id`, `organization_id` (FK)
- `key` (string, e.g. `admin`, `viewer`) — unique per org
- `name` (string), `description` (string)
- `permissions` (string array — keys from the global permission registry)
- `is_system` (bool) — `org:admin` and `org:member` are system roles, immutable.

### 4.14 `organization_domain` (email-domain auto-join)
- `id`, `organization_id` (FK)
- `domain` (string, unique per instance)
- `verification_token`, `verified_at`
- `enrollment_mode` enum(`public_invitation`, `automatic`, `manual`)

### 4.15 `api_key`
- `id`, `instance_id`
- `name` (string), `description` (string)
- `key_prefix` (string, 8 chars — for display)
- `key_hash` (string — argon2id of the secret)
- `scopes` (string array — e.g. `users:read`, `orgs:write`)
- `last_used_at` (timestamp, nullable)
- `revoked_at` (timestamp, nullable)
- `created_by` (user id)

### 4.16 `jwt_template`
- `id`, `instance_id`
- `name` (string, unique per instance)
- `algorithm` enum(`HS256`, `RS256`)
- `lifetime` (int seconds, default 3600)
- `claims` (JSONB — template with `{{user.id}}` etc.)
- `signing_key` (text, nullable — for HS256)

### 4.17 `oauth_application` (3rd-party apps that use gates as IdP)
- `id`, `instance_id`
- `name`, `client_id` (public), `client_secret_hash` (argon2id)
- `redirect_uris` (string array)
- `scopes` (string array)
- `homepage_url`, `logo_url`
- `created_at`

### 4.18 `oauth_consent`
- `id`, `oauth_application_id`, `user_id`
- `granted_scopes` (string array)
- `granted_at`, `revoked_at`

### 4.19 `verification`
Generic codes/tokens for email, SMS, password reset, magic link, etc.
- `id`, `instance_id`, `user_id` (nullable — e.g. signup)
- `type` enum(`email_verification`, `phone_verification`, `password_reset`, `magic_link`, `invitation`, `oauth_authorization`, `saml_slo`, `passkey_enrollment`, `mfa_enrollment`)
- `strategy` enum(`email_code`, `email_link`, `phone_code`, `totp`, `backup_code`, `webauthn`)
- `target` (string — email/phone/etc.)
- `code_hash` (nullable — for OTP)
- `token_hash` (nullable — for magic link / reset)
- `expires_at`, `consumed_at`, `attempts` (int)
- `metadata` (JSONB — extra context like `redirect_url`)

### 4.20 `audit_log`
- `id`, `instance_id`, `user_id` (nullable)
- `actor_type` enum(`user`, `api_key`, `system`, `oauth_app`)
- `actor_id` (string)
- `event` (string — e.g. `user.created`, `session.revoked`)
- `ip_address` (inet), `user_agent` (string)
- `metadata` (JSONB)
- `created_at`
- Partition by month in prod (declarative partitioning).

### 4.21 `webhook_endpoint` & `webhook_delivery`
- `endpoint.id`, `instance_id`, `url`, `secret_hash`, `events` (string array), `enabled`, `created_at`.
- `delivery.id`, `endpoint_id`, `event_id`, `payload` (JSONB), `response_status`, `response_body` (text), `attempt`, `delivered_at`, `next_retry_at` (exponential backoff up to 24h, 6 attempts).

### 4.22 `blocklist` (denylist for emails/domains/IPs)
- `id`, `instance_id`
- `type` enum(`email`, `domain`, `ip`, `phone`, `username`)
- `value` (citext / inet / string)
- `reason`, `created_by`, `created_at`

### 4.23 `rate_limit_bucket` (Redis-only, no DB row) — see §11.5

---

## 5. Authentication — every strategy Clerk supports

Every strategy below is a first-class flow with a dedicated service module. All flows return either a `Session` (logged in) or a `Verification` (requires further step).

### 5.1 Password (email + password)
- Endpoints: `POST /v1/sign_ups`, `POST /v1/sign_ins`, `POST /v1/passwords/reset`, `POST /v1/passwords/change`.
- Argon2id; default params: `m=64 MiB, t=3, p=4`, tunable per instance.
- Password policy per instance: min length (default 8), require upper/lower/digit/symbol, breached-password check (HaveIBeenPwned k-anonymity API), max length 128.
- Constant-time email enumeration prevention: `POST /v1/sign_ins` always takes the same time whether email exists or not; return identical response shape with `error: "form_password_incorrect"` regardless of cause.
- After 5 failed attempts within 15 min, lock account for 30 min (configurable). Increment `user.failed_attempts`, set `user.locked_until`.

### 5.2 Email magic link
- `POST /v1/sign_ins` with `strategy=magic_link` → enqueue email with single-use link.
- Token: 32 random bytes, base64url, stored hashed in `verification.token_hash`.
- TTL: 10 min default. Single use. Newest link invalidates older unconsumed ones for the same email.
- Link format: `https://<instance.host>/verify?token=...&redirect=...`.

### 5.3 Email OTP / SMS OTP
- `POST /v1/sign_ins` with `strategy=email_code` / `strategy=phone_code` → 6-digit code, TTL 10 min, max 5 attempts.
- Codes are numeric, no leading zeros are allowed in random gen to avoid confusion with `O`.
- Rate-limited per target (1 per 30s, 10 per hour).

### 5.4 Social OAuth (Google, GitHub, Apple, Microsoft)
- Each provider has a `Provider` class in `domains/oauth/`.
- Flow: `GET /v1/oauth/authorize?provider=google&redirect=...` → 302 to provider consent → callback at `GET /v1/oauth/callback/<provider>` → either:
  - New user: create `user` + `external_account`, return session.
  - Existing user with same email: **account linking flow** — email verification required before linking.
  - Existing user with `external_account` for same provider: just sign in.
- `authlib` does the heavy lifting; we only need per-provider client_id/secret in instance config and a normalization layer that maps provider payloads → `(provider_user_id, email, first_name, last_name, picture)`.
- All provider tokens encrypted at rest with Fernet; refresh-token rotation supported for Google, Microsoft, GitHub.

### 5.5 Passkeys (WebAuthn)
- Endpoints: `POST /v1/passkeys/registration/start`, `POST /v1/passkeys/registration/finish`, `POST /v1/passkeys/authentication/start`, `POST /v1/passkeys/authentication/finish`.
- Challenge: 32 random bytes, base64url, single-use, TTL 5 min.
- Discoverable credentials (resident keys) supported.
- User-Verified (`userVerification: required`) for sensitive flows.
- Backup-eligible / backup-state tracked per credential.
- Cross-device passkey (hybrid transport) supported.

### 5.6 SAML SSO (Enterprise connections)
- `SAMLConnection` table mirrors Clerk's Enterprise SSO: `id`, `instance_id`, `name`, `domains` (string array), `idp_entity_id`, `idp_sso_url`, `idp_certificate`, `sp_entity_id`, `acs_url`, `metadata_url` (auto-refresh), `attribute_mapping` (JSONB).
- `GET /v1/sso/saml/<connection_id>/acs` — SP-initiated and IdP-initiated.
- `POST /v1/sso/saml/<connection_id>/slo` — single logout.
- Signed AuthnRequests, verified Responses, encrypted assertions supported.

### 5.7 OIDC SSO (Enterprise connections)
- Generic OIDC provider config: `issuer`, `client_id`, `client_secret_enc`, `discovery_url`, `scopes`, `domain_aliases`, `attribute_mapping`.
- Same UX as SAML.

### 5.8 Multi-factor authentication
- **TOTP**: `pyotp` with SHA-1 (default), SHA-256, SHA-512. 6 digits, 30s period, 1-step clock skew tolerance. QR code returned as data URL.
- **SMS**: requires a verified phone number; same OTP flow as §5.3.
- **Backup codes**: 10 codes, one-time use, regeneratable. Displayed once on generation; stored as argon2 hashes.
- **MFA policy** per instance: `off`, `optional`, `required_for_admins`, `required`. When `required`, first sign-in without MFA triggers a `<MFAEnroll />` interstitial.
- Recovery: if a user loses all factors, the instance admin can issue a one-time MFA-bypass code via dashboard; this is audit-logged.

### 5.9 Username
- Optional identifier alongside or instead of email. Configurable per instance: `username_required`, `username_login_only` (no email).
- Regex `^[a-zA-Z0-9_.-]{3,32}$`, case-insensitive uniqueness.

### 5.10 Anonymous / guest
- `POST /v1/sign_ups` with `strategy=anonymous` → creates a user with no email/phone and a short-lived session.
- Upgrade flow: anon user can later add email/phone/password/etc. via the standard profile endpoints.

### 5.11 Impersonation
- Only callable by an authenticated admin via a `gates:*` server SDK.
- Returns a special session that is flagged `actor: { type: 'impersonation', admin_id: ... }` and exposed via `X-Gates-Actor` header on every downstream call.
- Audit-logged.

### 5.12 Sign-out
- `POST /v1/sessions/:id/revoke` — single session.
- `POST /v1/sessions/revoke_all` — all other sessions for the user.
- `POST /v1/sessions/end` — current session (sign out).

---

## 6. Sessions & tokens

### 6.1 Token shape (mimics Clerk's JWT)
Two tokens, both JWT (HS256 default, RS256 optional):
- **Client JWT** (in `__session` cookie or `Authorization: Bearer`):
  - `iss` = `https://<host>`
  - `sub` = `user.id`
  - `sid` = `session.id`
  - `iat`, `exp` (60 min)
  - `fva` (factor verification age, seconds) — used to enforce step-up auth
  - `org_id`, `org_role`, `org_permissions` (if a session is in an active org context)
  - `email`, `username`
- **Refresh token** (opaque, in `__session_refresh` httpOnly cookie): 32 random bytes, base64url, rotated on every refresh. TTL 60 days. Stored hashed in Redis with key `session:<id>:refresh`.

### 6.2 Cookie flags
- `HttpOnly`, `Secure`, `SameSite=Lax` (default; `None` for cross-origin if configured).
- Domain configurable per instance (`GATES_COOKIE_DOMAIN`).

### 6.3 Session lifecycle
- Idle timeout: 7 days of inactivity → session marked `expired`.
- Absolute timeout: 60 days from creation.
- Revocation: manual, on password change, on account deletion, on instance admin action.
- Concurrent sessions: allowed (mirroring Clerk). Per-user listing + remote revoke in dashboard.

### 6.4 Step-up authentication
Endpoints that perform sensitive actions (e.g. add MFA, change password, delete account) require a session where `now - fva < 600` (10 min, configurable). Otherwise respond with `403 step_up_required` and the SDK triggers a re-auth modal.

### 6.5 Active organization
- A session has an "active org" selected by `X-Gates-Organization-Id` header on incoming requests.
- Used to scope `org_role` and `org_permissions` claims in the JWT.
- `GET /v1/users/me/organizations` lists memberships; `GET /v1/organizations/:id/active` sets it for the session (returns updated cookie/JWT).

---

## 7. Public REST API (`/v1/*`)

All endpoints are versioned. Path + method + Clerk-style camelCase JSON. Errors: `{ "errors": [{ "code": "...", "message": "...", "long_message": "...", "meta": {...} }] }`.

### 7.1 Authentication
- `POST /v1/sign_ups`
- `POST /v1/sign_ins`
- `POST /v1/sign_outs`
- `POST /v1/tokens` — exchange refresh for access
- `POST /v1/verifications` — start email/phone/etc. verification
- `POST /v1/verifications/:id/attempt` — submit code
- `POST /v1/verifications/:id/finalize` — consume token
- `POST /v1/passwords/reset`
- `POST /v1/passwords/change`
- `GET  /v1/oauth/authorize`
- `GET  /v1/oauth/callback/:provider`
- `POST /v1/sso/saml/:connection/acs`

### 7.2 Users
- `GET    /v1/users`
- `POST   /v1/users`
- `GET    /v1/users/:id`
- `PATCH  /v1/users/:id`
- `DELETE /v1/users/:id`
- `GET    /v1/users/:id/email_addresses`
- `POST   /v1/users/:id/email_addresses`
- `PATCH  /v1/users/:id/email_addresses/:email_id`
- `DELETE /v1/users/:id/email_addresses/:email_id`
- `GET    /v1/users/:id/phone_numbers`
- `POST   /v1/users/:id/phone_numbers`
- `PATCH  /v1/users/:id/phone_numbers/:phone_id`
- `DELETE /v1/users/:id/phone_numbers/:phone_id`
- `GET    /v1/users/:id/external_accounts`
- `DELETE /v1/users/:id/external_accounts/:external_id`
- `GET    /v1/users/:id/sessions`
- `GET    /v1/users/:id/passkeys`
- `POST   /v1/users/:id/passkeys`
- `DELETE /v1/users/:id/passkeys/:passkey_id`
- `GET    /v1/users/:id/mfa_factors`
- `POST   /v1/users/:id/mfa_factors`
- `PATCH  /v1/users/:id/mfa_factors/:factor_id`
- `DELETE /v1/users/:id/mfa_factors/:factor_id`
- `POST   /v1/users/:id/ban`
- `POST   /v1/users/:id/unban`
- `POST   /v1/users/:id/lock`
- `POST   /v1/users/:id/unlock`
- `POST   /v1/users/:id/impersonate`

### 7.3 Sessions
- `GET    /v1/sessions`
- `GET    /v1/sessions/:id`
- `PATCH  /v1/sessions/:id` (e.g. active org)
- `POST   /v1/sessions/:id/revoke`
- `POST   /v1/sessions/:id/refresh`
- `POST   /v1/sessions/revoke_all`
- `GET    /v1/sessions/:id/tokens`

### 7.4 Organizations
- `GET    /v1/organizations`
- `POST   /v1/organizations`
- `GET    /v1/organizations/:id`
- `PATCH  /v1/organizations/:id`
- `DELETE /v1/organizations/:id`
- `GET    /v1/organizations/:id/memberships`
- `POST   /v1/organizations/:id/memberships`
- `PATCH  /v1/organizations/:id/memberships/:user_id`
- `DELETE /v1/organizations/:id/memberships/:user_id`
- `GET    /v1/organizations/:id/invitations`
- `POST   /v1/organizations/:id/invitations`
- `POST   /v1/organizations/:id/invitations/bulk`
- `GET    /v1/organizations/:id/invitations/:inv_id`
- `POST   /v1/organizations/:id/invitations/:inv_id/revoke`
- `POST   /v1/organizations/:id/invitations/accept` (token-based)
- `GET    /v1/organizations/:id/domains`
- `POST   /v1/organizations/:id/domains`
- `GET    /v1/organizations/:id/domains/:domain_id`
- `DELETE /v1/organizations/:id/domains/:domain_id`
- `POST   /v1/organizations/:id/domains/:domain_id/verify`
- `GET    /v1/organizations/:id/roles`
- `POST   /v1/organizations/:id/roles`
- `PATCH  /v1/organizations/:id/roles/:role_id`
- `DELETE /v1/organizations/:id/roles/:role_id`

### 7.5 Instance config / dev
- `GET    /v1/instance` — public info (auth methods, branding)
- `GET    /v1/jwks` — public keys for token verification
- `GET    /v1/jwt_templates`
- `POST   /v1/jwt_templates`
- `PATCH  /v1/jwt_templates/:id`
- `DELETE /v1/jwt_templates/:id`
- `GET    /v1/api_keys`
- `POST   /v1/api_keys`
- `DELETE /v1/api_keys/:id` (revoke)
- `GET    /v1/blocklist_identifiers`
- `POST   /v1/blocklist_identifiers`
- `DELETE /v1/blocklist_identifiers/:id`
- `GET    /v1/audit_logs`
- `GET    /v1/webhooks/endpoints`
- `POST   /v1/webhooks/endpoints`
- `PATCH  /v1/webhooks/endpoints/:id`
- `DELETE /v1/webhooks/endpoints/:id`
- `GET    /v1/webhooks/endpoints/:id/deliveries`

### 7.6 OAuth-as-IdP
- `GET    /v1/oauth_applications`
- `POST   /v1/oauth_applications`
- `PATCH  /v1/oauth_applications/:id`
- `DELETE /v1/oauth_applications/:id`
- `GET    /v1/oauth_authorize`
- `POST   /v1/oauth_authorize/decision`
- `POST   /v1/oauth_token`
- `GET    /v1/oauth_userinfo`

---

## 8. Webhooks (outgoing)

Events follow Clerk's taxonomy. The full list is in `src/gates/webhooks/events.py`. Examples:
`user.created`, `user.updated`, `user.deleted`, `session.created`, `session.revoked`, `session.ended`, `email.created`, `email.verified`, `phone.created`, `phone.verified`, `organization.created`, `organization.updated`, `organization.deleted`, `organizationMembership.created`, `organizationMembership.updated`, `organizationMembership.deleted`, `organizationInvitation.created`, `organizationInvitation.accepted`, `organizationInvitation.revoked`, `samlConnection.created`, `samlConnection.updated`, `samlConnection.deleted`, `passkey.created`, `passkey.deleted`, `mfaFactor.enabled`, `mfaFactor.disabled`, `apiKey.created`, `apiKey.deleted`.

Delivery:
- HMAC-SHA256 of the raw body using the endpoint secret, header `Gates-Signature: t=<unix_ts>,v1=<hex>`.
- Replay protection: reject if `abs(now - t) > 300s`.
- Retry: 6 attempts, backoff 30s, 5m, 30m, 2h, 8h, 24h, then marked `failed`.
- Manual replay: `POST /v1/webhooks/endpoints/:id/deliveries/:delivery_id/redeliver`.

---

## 9. Frontend drop-in components (`@gates/react`, `@gates/nextjs`)

All components are headless-friendly: a `appearance` prop with `variables`, `elements`, `layout` keys (mirrors Clerk). All text is i18n via a `localization` prop with English as default and a translation file format identical to Clerk's.

### 9.1 Core
- `<GatesProvider publishableKey="pk_...">` — sets up client, React context, Clerk-compatible `__session` cookie.
- `<SignedIn>`, `<SignedOut>` — render children conditionally.
- `<Protect role="org:admin" permission="org:read" requireSession>` — render only when checks pass.
- `useAuth()`, `useUser()`, `useSession()`, `useOrganization()`, `useOrganizationList()` — React hooks.

### 9.2 Authentication components
- `<SignIn />` — modal/inline/redirect modes. Props: `routing="hash"|"path"|"virtual"`, `afterSignInUrl`, `signUpUrl`, `appearance`.
- `<SignUp />` — same shape.
- `<UserButton />` — avatar + dropdown (manage account, switch org, sign out).
- `<UserProfile />` — full account page (emails, phones, connected accounts, passkeys, MFA, sessions, danger zone).
- `<OrganizationSwitcher />`, `<OrganizationProfile />`, `<OrganizationList />`, `<CreateOrganization />`.

### 9.3 Component package boundaries
- `@gates/react` — pure components, framework-agnostic state.
- `@gates/nextjs` — server helpers: `auth()` for App Router server components, `currentUser()`, middleware (`createRouteMatcher`, `gatesMiddleware` for `middleware.ts`).
- `@gates/remix` — loader/action helpers.

### 9.4 Hosted pages fallback
When the consumer does not want a custom UI, gates serves hosted pages at:
- `/sign-in`, `/sign-up`, `/verify`, `/forgot-password`, `/reset-password`, `/sso-callback`, `/oauth-callback/:provider`, `/user/profile`, `/user/security`, `/org-profile`, `/org/new`, `/org/select`.

---

## 10. Permissions & roles

### 10.1 System permissions (global registry, immutable)
Stored in `src/gates/domains/roles/registry.py`. Format `resource:action`. Examples:
- `org:read`, `org:manage`, `org:delete`, `org:create`
- `org:member:read`, `org:member:manage`
- `org:invitation:read`, `org:invitation:create`, `org:invitation:revoke`
- `org:domain:read`, `org:domain:manage`
- `org:role:read`, `org:role:manage`
- `user:read`, `user:create`, `user:update`, `user:delete`
- `user:ban`, `user:impersonate`
- `session:read`, `session:revoke`
- `webhook:read`, `webhook:manage`
- `api_key:read`, `api_key:manage`
- `billing:read`, `billing:manage`

### 10.2 System roles
- `org:admin` — all `org:*` permissions.
- `org:member` — `org:read`, `org:member:read`.
- `basic_member` — same as `org:member` (alias for clarity).

### 10.3 Custom roles
Per organization, created via API/dashboard. Must include ≥ 1 permission. `is_system=true` is read-only.

### 10.4 API-key scopes
- Mirror the global permission set with a `gates:` prefix (e.g. `gates:users:read`, `gates:orgs:write`).
- `gates:*` wildcard for full access (super-admin only).
- Enforced in a FastAPI dependency: `require_scopes("gates:users:read")`.

### 10.5 Enforcement
- Every router function declares required permissions via dependency.
- Service layer re-checks (defence in depth): no `gates:` call reaches the DB without passing through `assert_can(actor, resource, action)`.

---

## 11. Security requirements (non-negotiable)

### 11.1 Password hashing
Argon2id, `m=64 MiB, t=3, p=4`. Passwords are never logged, never returned in API responses. Verified via `argon2-cffi`'s constant-time `verify`.

### 11.2 Field-level encryption (at rest)
All OAuth tokens, MFA seeds, webhook secrets, JWT template signing keys, OAuth client secrets are encrypted with **Fernet** (AES-128-CBC + HMAC-SHA256). Key from `GATES_FIELD_ENCRYPTION_KEY` (32-byte url-safe base64). Key rotation supported via `previous_keys` array — `decrypt` tries each in order, `encrypt` always uses current.

### 11.3 Token signing
- HS256 by default (shared secret in env).
- RS256 optional per instance — generate keypair, expose public key at `GET /v1/jwks`.
- Tokens are short-lived (60 min), refresh tokens are opaque + rotated.

### 11.4 CSRF
- Cookie-based auth uses `SameSite=Lax` and a double-submit CSRF token on state-changing requests.
- The CSRF token is exposed via the `X-CSRF-Token` response header and the `<GatesProvider>` reads it.

### 11.5 Rate limiting (Redis token bucket)
Per-IP and per-actor, per-endpoint, configurable per instance. Defaults:
- `POST /v1/sign_ins` — 30/min per IP, 5/min per email.
- `POST /v1/sign_ups` — 10/min per IP.
- `POST /v1/verifications` — 5/min per target, 20/hour per user.
- `POST /v1/oauth/...` — 60/min per IP.
- `POST /v1/webhooks/...` admin — 10/min per admin.
- Global per-instance: 1000 req/sec (configurable).

Implemented in `core/ratelimit.py` with a Lua-script-backed token bucket. Returns `429` with `Retry-After` and `X-RateLimit-*` headers.

### 11.6 Brute-force / lockout
- 5 failed sign-in attempts within 15 min → user locked for 30 min.
- Lockout is per `(user, ip)` — different IPs don't share a counter.
- Unlock via `POST /v1/users/:id/unlock` (admin) or successful password reset.

### 11.7 Bot protection
- Optional Turnstile / hCaptcha / reCAPTCHA on `sign_ups` and `password_reset`.
- Frontend `GatesProvider` accepts a `captchaSiteKey` and the components embed the widget.
- Verification token validated server-side before issuing the verification.

### 11.8 Audit logging
Every state-changing API call writes to `audit_log` with: actor, IP, UA, event code, before/after diff for `update` events. Retention configurable per instance (default 365 days). Read-only via `GET /v1/audit_logs` (paginated, filterable).

### 11.9 Secrets handling
- `.env` for dev only. Production secrets read from env, never committed.
- A `secrets-doctor` CLI command audits config at boot and warns about weak/default secrets.
- No secret in logs, ever. Use `***` redaction in `core/security.redact()`.

### 11.10 Headers
Every response sets:
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` on hosted pages (strict default, configurable).
- `Permissions-Policy: ...` minimal.

### 11.11 GDPR
- `GET /v1/users/:id?private_metadata=true` to export everything.
- `DELETE /v1/users/:id` — soft delete for 30 days, then hard delete with `gated_purge: true` job.
- IP addresses stored as `inet`; configurable retention; auto-purge old sessions on TTL.

### 11.12 Compliance posture (v1)
- SOC 2 Type II readiness: audit logs, RBAC, encryption, change management.
- HIPAA: PHI never stored in `private_metadata` by default; signed BAA required (out of code, in deployment).

---

## 12. SDK contract (server side)

Every server SDK exposes:
```python
# server-python / FastAPI
from gates_server import gates, require_auth, require_org_role, require_permission

app = FastAPI()

@gates()
@app.get("/me")
@require_auth
async def me(request: Request):
    return await request.state.gates.user()

@app.post("/articles")
@require_auth
@require_org_role("org:admin")
async def create_article(request: Request):
    ...
```

Internals: the SDK validates the JWT, checks the signing key against `GATES_JWT_KEY` or fetches `/v1/jwks`, populates `request.state.gates = { user, session, organization, has(perm) }`, and the decorators do the RBAC.

---

## 13. Configuration

`.env.example`:
```
GATES_ENV=development
GATES_HOST=localhost:8000
GATES_PUBLIC_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://gates:gates@localhost:5432/gates
REDIS_URL=redis://localhost:6379/0
GATES_FIELD_ENCRYPTION_KEY= # 32-byte url-safe base64
GATES_JWT_SIGNING_KEY= # HS256 secret, or
GATES_JWT_SIGNING_KEY_PATH= # RS256 private key
GATES_COOKIE_DOMAIN=localhost
GATES_COOKIE_SECURE=false
GATES_EMAIL_PROVIDER=postmark
POSTMARK_TOKEN=
SES_REGION=us-east-1
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_BUCKET=gates
GATES_CAPTCHA_PROVIDER=turnstile
GATES_TURNSTILE_SECRET=
GATES_WEBHOOK_TIMEOUT=10
```

Loaded via `pydantic-settings` into a frozen `Settings` singleton; never mutate at runtime.

---

## 14. Scope flags

| Area                                  | v1 status        |
| ------------------------------------- | ---------------- |
| Email + password, magic link, OTP     | IN SCOPE         |
| Social OAuth (Google, GitHub, Apple, Microsoft) | IN SCOPE |
| Other social providers (Facebook, X, Discord, Slack, etc.) | OUT OF SCOPE v1 (generic OAuth2 interface in place) |
| Passkeys (WebAuthn)                   | IN SCOPE         |
| TOTP MFA                              | IN SCOPE         |
| SMS MFA                               | IN SCOPE         |
| Backup codes                          | IN SCOPE         |
| SAML SSO                              | IN SCOPE         |
| OIDC SSO                              | IN SCOPE         |
| Organizations + RBAC                  | IN SCOPE         |
| Org invitations + email-domain auto-join | IN SCOPE     |
| Custom roles + permissions            | IN SCOPE         |
| Sessions (JWT + refresh)              | IN SCOPE         |
| Step-up auth                          | IN SCOPE         |
| Impersonation                         | IN SCOPE         |
| Webhooks (outgoing, signed, retried)  | IN SCOPE         |
| API keys (server-to-server)           | IN SCOPE         |
| JWT templates                         | IN SCOPE         |
| OAuth-as-IdP (gates as IdP for 3rd-party apps) | IN SCOPE |
| Audit logs                            | IN SCOPE         |
| Blocklist                             | IN SCOPE         |
| Rate limiting + bot protection        | IN SCOPE         |
| Drop-in React/Next/Remix components   | IN SCOPE         |
| Hosted pages fallback                 | IN SCOPE         |
| Dashboard (tenant admin UI)           | IN SCOPE         |
| Billing / plans (Clerk Billing parity) | OUT OF SCOPE v1  |
| Machine-to-machine tokens (Clerk M2M) | OUT OF SCOPE v1  |
| WorkOS / Oauth enterprise onboarding portal | OUT OF SCOPE v1 |
| Mobile native SDKs (iOS/Android)      | OUT OF SCOPE v1  |

For every OUT OF SCOPE item, leave a clearly marked stub module + tests skipped with `@pytest.mark.skip(reason="v2")` so the next agent can fill it in.

---

## 15. Implementation phases (suggested order)

1. **Skeleton** — FastAPI app, settings, DB session, Alembic, healthcheck, `core.errors`, `core.security` (argon2, Fernet, JWT). Docker compose up. `GET /health` returns 200.
2. **Users + passwords** — `users`, `passwords`, `email_addresses` domains + sign-up / sign-in / password-reset endpoints. Argon2 hashing. Constant-time responses.
3. **Sessions + tokens** — JWT issuance, refresh, revoke, cookie handling, step-up.
4. **Webhooks** — endpoints, deliveries, signing, retries.
5. **API keys + RBAC** — `api_keys`, `require_scopes`, audit log foundation.
6. **Email magic link + OTP** — `magic_links`, `otp` domains, Postmark integration.
7. **SMS OTP** — Twilio integration, `phone_numbers` domain.
8. **Social OAuth (Google + GitHub first, then Apple + Microsoft)**.
9. **MFA — TOTP + backup codes**.
10. **Passkeys (WebAuthn)**.
11. **Organizations + invitations + roles + permissions**.
12. **Org domain verification + auto-join**.
13. **SAML + OIDC SSO**.
14. **Frontend SDKs — `useAuth`, `useUser`, `<GatesProvider>`, `<SignIn>`, `<SignUp>`, `<UserButton>`, `<UserProfile>`**.
15. **Hosted pages** (server-rendered HTMX or React SSR).
16. **Dashboard (tenant admin UI)**.
17. **Impersonation, blocklist, account linking, anonymous users**.
18. **OAuth-as-IdP**.
19. **JWT templates**.
20. **Bot protection, advanced rate limiting, security headers**.
21. **Audit log UI + GDPR export**.
22. **Hardening pass: fuzz tests, OWASP ASVS audit, load test (k6), docs site**.

Each phase ends with: passing tests, an updated OpenAPI spec at `/openapi.json`, and a changelog entry.

---

## 16. Testing rules

- Every service module has a `tests/test_service.py` with happy + each error path.
- Every router has a `tests/test_router.py` that exercises the API surface as a black box.
- Fixtures in `conftest.py` provide a fresh DB per test (transactional rollback) and a `gates_client` (`httpx.AsyncClient`) pre-authed as a test admin.
- Use `time_machine` or a `clock` fixture for any time-sensitive test (lockouts, expirations).
- For OAuth tests, use `authlib`'s mocking helpers or a `responses`/`respx` mock.
- E2E: `playwright` covers sign-up, sign-in, MFA enroll, passkey flow, org invite, webhook delivery.
- Coverage: `pytest --cov=gates --cov-fail-under=85` in CI.

---

## 17. Documentation deliverables (per feature)

Every feature PR must include:
- A `docs/<feature>.md` with: overview, API, SDK examples (React + server), webhook events, edge cases.
- An entry in `CHANGELOG.md`.
- An OpenAPI diff (`/openapi.json` before/after).
- A test plan and a security review note (e.g. "no new PII storage; rate-limited at 5/min/IP").

---

## 18. Glossary (match Clerk's vocabulary)

| gates term          | Clerk term              | Notes                          |
| ------------------- | ----------------------- | ------------------------------ |
| instance            | instance                | dev / staging / prod           |
| gates               | Clerk                   | brand                          |
| user                | user                    |                                |
| email_address       | email_address           |                                |
| phone_number        | phone_number            |                                |
| external_account    | external_account        |                                |
| verification        | verification            |                                |
| session             | session                 |                                |
| mfa_factor          | phone_code, totp        |                                |
| organization        | organization            |                                |
| organization_membership | organization_membership |                            |
| role                | role                    |                                |
| api_key             | api_key                 |                                |
| jwt_template        | jwt_template            |                                |
| webhook_endpoint    | webhook                 |                                |
| audit_log           | event log (admin UI)    |                                |
| blocklist           | blocklist               |                                |
| impersonation       | impersonation           |                                |

**Vocabulary lock:** Do not invent new public names. If Clerk's term fits, use it. If you genuinely need a new term, add it here and to `DECISIONS.md`.

---

## 19. Anti-patterns (forbidden)

- ❌ Storing plaintext passwords, OAuth tokens, MFA seeds, or webhook secrets.
- ❌ Logging full request bodies, response bodies, or tokens.
- ❌ Letting a `404` vs `401` reveal whether an email/user exists. Always return a single `form_*_incorrect` shape.
- ❌ Doing any business logic in a FastAPI route handler.
- ❌ Using `int` for IDs in the public API. Use string `cuid2`.
- ❌ Returning `password_hash` or any encrypted secret in any API response.
- ❌ Mutable global state (no module-level dicts holding sessions, rate-limit counters, etc.).
- ❌ New SQL written outside `service.py` files.
- ❌ New dependencies added without an entry in `pyproject.toml` and a rationale in the PR.
- ❌ Skipping tests. PRs without tests will be rejected.

---

## 20. Definition of Done (per PR)

A PR is done when:
1. All acceptance criteria in the corresponding AGENTS.md section are met.
2. `ruff check`, `mypy`, `pytest`, `pytest --cov` pass in CI.
3. OpenAPI spec is updated and committed.
4. `docs/<feature>.md` is updated.
5. A demo screenshot or curl trace is attached for any UI or end-to-end flow change.
6. `DECISIONS.md` is updated if any design choice was made.
7. The PR description links to this file's section number.

---

## 21. Quick start for a new agent

```bash
# clone, then:
cp .env.example .env
docker compose up -d postgres redis mailhog minio
uv sync
uv run alembic upgrade head
uv run uvicorn gates.main:app --reload

# tests:
uv run pytest -q
uv run pytest --cov=gates --cov-fail-under=85
```

Open `http://localhost:8000/docs` for the OpenAPI UI, `http://localhost:8025` for Mailhog, `http://localhost:9001` for Minio console.

If anything in this document is wrong, **fix this document first** (PR titled `docs(agents): correct ...`) and only then implement. The document is the source of truth.
