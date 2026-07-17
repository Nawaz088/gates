# Architecture Decision Log

## ADR-001: Tech stack
**Date:** 2025-07-18
**Decision:** Python 3.12 + FastAPI + SQLAlchemy 2.x async + PostgreSQL 16 + Redis 7
**Rationale:** Best ecosystem match for an auth platform needing async perf, strong typing, and broad library support.

## ADR-002: ID format
**Date:** 2025-07-18
**Decision:** User-facing entities use cuid2 (24-char case-sensitive base36); internal join rows use UUIDv7.
**Rationale:** cuid2 is URL-safe, unguessable, and collision-resistant without centralized coordination. UUIDv7 is time-sortable for internal indexing.

## ADR-003: API naming convention
**Date:** 2025-07-18
**Decision:** Public REST API uses Clerk's camelCase (`firstName`, `lastName`); DB and Pydantic models use snake_case with Pydantic aliases.
**Rationale:** Developer familiarity; Clerk's naming is the market standard.

## ADR-004: Token strategy
**Date:** 2025-07-18
**Decision:** Short-lived JWT (60 min, HS256 default, RS256 optional) + opaque rotated refresh token (60 days, stored hashed in Redis).
**Rationale:** JWTs enable stateless verification by downstream services; opaque refresh tokens are more secure (rotated, stored hashed).

## ADR-005: Password hashing
**Date:** 2025-07-18
**Decision:** Argon2id with `m=64MiB, t=3, p=4` tunable per instance.
**Rationale:** OWASP-recommended; resistant to GPU/ASIC attacks.

## ADR-006: At-rest encryption
**Date:** 2025-07-18
**Decision:** Fernet (AES-128-CBC + HMAC-SHA256) for all secrets (OAuth tokens, MFA seeds, webhook secrets, API key hashes).
**Rationale:** Simple, well-audited, supports key rotation via `previous_keys`.

## ADR-007: Frontend components
**Date:** 2025-07-18
**Decision:** React 18 + TypeScript + Vite for SDK; Tailwind + Radix UI for styling.
**Rationale:** Largest ecosystem, maximum recruiter/contributor reach. Radix provides accessible headless primitives; Tailwind keeps bundle small.

## ADR-008: Multi-instance multi-tenancy
**Date:** 2025-07-18
**Decision:** Row-level multi-tenancy via `instance_id` FK on every entity (discriminator column), NOT separate databases.
**Rationale:** Simpler operations, shared connection pool, unified migrations.
