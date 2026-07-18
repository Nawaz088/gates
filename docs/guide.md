# Gates — Authentication Platform User Guide

> A self-hostable, full-featured authentication and user-management platform — a Clerk alternative.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Configuration](#configuration)
4. [Backend Integration (Server SDK)](#backend-integration)
5. [Frontend Integration (React SDK)](#frontend-integration)
6. [Next.js Integration](#nextjs-integration)
7. [Authentication Flows](#authentication-flows)
8. [API Reference](#api-reference)
9. [Webhooks](#webhooks)
10. [Organizations & RBAC](#organizations--rbac)
11. [Deployment](#deployment)
12. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7
- Node.js 20+ (for frontend SDKs)

### 1. Clone & Install

```bash
git clone <your-repo> gates
cd gates
cp .env.example .env

# Start dependencies
docker compose up -d postgres redis mailhog minio

# Install Python dependencies
uv sync --all-extras

# Run database migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn gates.main:app --reload
```

The API is now running at `http://localhost:8000`. Open `http://localhost:8000/docs` for the interactive OpenAPI documentation.

### 2. Verify it works

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"gates"}

curl -X POST http://localhost:8000/v1/sign_ups \
  -H "Content-Type: application/json" \
  -d '{"email_address":["user@example.com"],"password":"my-secure-password"}'
```

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  Your App   │────▶│  Gates API   │────▶│ PostgreSQL │
│  (React/Vue)│     │  (FastAPI)   │     │            │
│  + SDK      │◀────│  :8000       │◀────│  :5432     │
└─────────────┘     └──────┬───────┘     └────────────┘
                           │
                    ┌──────▼───────┐     ┌────────────┐
                    │  Redis       │     │  MinIO/S3  │
                    │  :6379       │     │  :9000     │
                    └──────────────┘     └────────────┘
```

- **Session tokens**: JWT (60 min) + opaque refresh token (60 days) stored in cookies
- **API keys**: `gates_`-prefixed tokens for server-to-server auth
- **Webhooks**: Outgoing event-based HTTP calls with HMAC-SHA256 signing

---

## Configuration

All configuration is via environment variables (see `.env.example`):

```env
# Instance
GATES_ENV=development
GATES_HOST=0.0.0.0
GATES_PORT=8000
GATES_PUBLIC_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql+asyncpg://gates:gates@localhost:5432/gates

# Redis
REDIS_URL=redis://localhost:6379/0

# Encryption (generate with: openssl rand -base64 32)
GATES_FIELD_ENCRYPTION_KEY=<32-byte-base64>

# JWT Signing
GATES_JWT_SIGNING_KEY=<your-secret-at-least-32-chars>

# Email (Postmark or SES)
POSTMARK_TOKEN=<your-postmark-token>

# SMS (Twilio)
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>

# S3 (avatars, attachments)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_BUCKET=gates

# Bot protection
GATES_CAPTCHA_PROVIDER=turnstile   # or recaptcha, hcaptcha
GATES_TURNSTILE_SECRET=<secret>
```

---

## Backend Integration

### Using the Server SDK (Python / FastAPI)

```python
from fastapi import FastAPI, Request, Depends
from gates_server import gates, require_auth, require_org_role

app = FastAPI()

@gates()
@app.get("/me")
@require_auth
async def my_profile(request: Request):
    """Only authenticated users can access this."""
    user = request.state.gates.user()
    return {"id": user.id, "email": user.email}

@gates()
@app.post("/admin/users")
@require_auth
@require_org_role("org:admin")
async def admin_only(request: Request):
    """Only org admins can access this."""
    return {"status": "ok"}
```

### Manual JWT Verification (any language)

```python
import jwt

# Fetch the JWKS from
# GET /v1/jwks
# Then verify
payload = jwt.decode(
    token,
    key=<public-key-or-secret>,
    algorithms=["HS256"],
    audience="https://your-gates-instance.com",
)
user_id = payload["sub"]
session_id = payload["sid"]
```

### API Key Authentication (server-to-server)

```bash
# Create an API key
curl -X POST http://localhost:8000/v1/api_keys \
  -H "Authorization: Bearer <your-session-token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Service","scopes":["gates:users:read","gates:orgs:write"]}'

# Use it
curl http://localhost:8000/v1/users \
  -H "Authorization: Bearer gates_abc123..."
```

---

## Frontend Integration

### React (Vite / CRA / Remix)

#### 1. Install

```bash
npm install @gates/react
# or
pnpm add @gates/react
```

#### 2. Wrap your app

```tsx
import { GatesProvider } from "@gates/react";

export default function Root({ children }) {
  return (
    <GatesProvider publishableKey="pk_test_...">
      {children}
    </GatesProvider>
  );
}
```

#### 3. Use the hooks

```tsx
import { useAuth, useUser, useSession } from "@gates/react";

function Profile() {
  const { isSignedIn, signOut, openSignIn } = useAuth();
  const { user } = useUser();
  const { session } = useSession();

  if (!isSignedIn) {
    return <button onClick={openSignIn}>Sign In</button>;
  }

  return (
    <div>
      <p>Welcome, {user?.firstName}!</p>
      <p>Session: {session?.id}</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  );
}
```

#### 4. Conditional rendering

```tsx
import { SignedIn, SignedOut, Protect } from "@gates/react";

function Nav() {
  return (
    <nav>
      <SignedIn>
        <a href="/dashboard">Dashboard</a>
        <a href="/profile">Profile</a>
      </SignedIn>
      <SignedOut>
        <a href="/sign-in">Sign In</a>
        <a href="/sign-up">Sign Up</a>
      </SignedOut>

      <Protect role="org:admin">
        <a href="/admin">Admin Panel</a>
      </Protect>
    </nav>
  );
}
```

#### 5. Sign-in / Sign-up components

```tsx
import { SignIn, SignUp, UserButton, UserProfile } from "@gates/react";

function AuthPage() {
  return (
    <div>
      <SignIn
        routing="path"                // "hash" | "path" | "virtual"
        afterSignInUrl="/dashboard"
        signUpUrl="/sign-up"
      />
    </div>
  );
}

function AppHeader() {
  return (
    <header>
      <UserButton />  {/* Avatar + dropdown with sign-out */}
    </header>
  );
}

function SettingsPage() {
  return <UserProfile />;  {/* Full account management */}
}
```

---

## Next.js Integration

### 1. Install

```bash
npm install @gates/nextjs @gates/react
```

### 2. Provider (layout)

```tsx
// app/layout.tsx
import { GatesProvider } from "@gates/react";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <GatesProvider publishableKey="pk_test_...">
          {children}
        </GatesProvider>
      </body>
    </html>
  );
}
```

### 3. Server components

```tsx
// app/page.tsx
import { auth, currentUser } from "@gates/nextjs";

export default async function Home() {
  const { userId, isSignedIn, orgRole } = await auth();
  const user = await currentUser();

  return (
    <div>
      {isSignedIn ? (
        <p>Welcome back, {user?.email}</p>
      ) : (
        <p>Please sign in</p>
      )}
    </div>
  );
}
```

### 4. Middleware

```ts
// middleware.ts
import { auth, createRouteMatcher } from "@gates/nextjs";
import { NextResponse } from "next/server";

const protectedRoutes = createRouteMatcher([
  "/dashboard(.*)",
  "/api/protected(.*)",
]);

export default async function middleware(request: Request) {
  const { isSignedIn } = await auth();

  if (protectedRoutes(new URL(request.url).pathname) && !isSignedIn) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|sign-in|sign-up).*)"],
};
```

---

## Authentication Flows

### Email + Password (default)

```
POST /v1/sign_ups       → creates user + email + session
POST /v1/sign_ins        → validates credentials, issues session
POST /v1/sign_outs       → revokes current session, clears cookies
```

### Magic Link

```
POST /v1/verifications   → with strategy:"email_link"
  → sends email with single-use link
GET /verify?token=...    → validates token, issues session
```

### OTP (Email/SMS)

```
POST /v1/verifications   → with strategy:"email_code" or "phone_code"
  → sends 6-digit code
POST /v1/verifications/:id/attempt  → submit code, max 5 attempts
```

### Social OAuth

```
GET  /v1/oauth/authorize?provider=google → 302 to Google consent
GET  /v1/oauth/callback/google?code=...  → exchanges code, creates session
```

Supported providers: `google`, `github`, `apple`, `microsoft`.

### Passkeys (WebAuthn)

```
POST /v1/passkeys/registration/start     → returns challenge + options
POST /v1/passkeys/registration/finish    → verifies credential, stores passkey
POST /v1/passkeys/authentication/start   → returns allow_credentials + challenge
POST /v1/passkeys/authentication/finish  → verifies assertion, signs in
```

### MFA (TOTP)

```
POST /v1/users/:id/mfa_factors                       → enroll, get provisioning_uri
POST /v1/users/:id/mfa_factors/:factor_id/verify     → verify TOTP code
POST /v1/users/:id/mfa_factors/challenge              → verify during sign-in
```

### SSO (SAML)

```
GET  /v1/sso/saml/:id/login     → SP-initiated SSO redirect
POST /v1/sso/saml/:id/acs       → Assertion Consumer Service
GET  /v1/sso/saml/:id/slo       → Single Logout
```

### SSO (OIDC)

```
GET  /v1/sso/oidc/:id/authorize → redirect to IdP
POST /v1/sso/oidc/:id/callback  → handle authorization code
```

### Impersonation

```
POST /v1/users/:id/impersonate  → issue session as target user (admin only)
```

### Anonymous Users

```
POST /v1/sign_ups with strategy:"anonymous"
  → creates user with no email/password, issues short-lived session
```

---

## API Reference

All endpoints are under `/v1/*`. Full OpenAPI spec at `http://localhost:8000/docs`.

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/sign_ups` | Create account |
| POST | `/v1/sign_ins` | Sign in |
| POST | `/v1/sign_outs` | Sign out (revoke session) |
| POST | `/v1/tokens` | Exchange refresh token for new JWT |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/users` | List users (admin) |
| POST | `/v1/users` | Create user (admin) |
| GET | `/v1/users/:id` | Get user |
| PATCH | `/v1/users/:id` | Update user |
| DELETE | `/v1/users/:id` | Delete user |
| POST | `/v1/users/:id/ban` | Ban user |
| POST | `/v1/users/:id/unban` | Unban user |
| POST | `/v1/users/:id/lock` | Lock user (brute-force) |
| POST | `/v1/users/:id/unlock` | Unlock user |
| POST | `/v1/users/:id/impersonate` | Impersonate user |

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/sessions` | List sessions |
| GET | `/v1/sessions/:id` | Get session |
| POST | `/v1/sessions/:id/revoke` | Revoke session |
| POST | `/v1/sessions/revoke_all` | Revoke all other sessions |
| POST | `/v1/sessions/:id/refresh` | Refresh session tokens |

### Email & Phone

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/v1/users/:id/email_addresses` | Manage emails |
| POST | `/v1/users/:id/email_addresses/:id/verify` | Verify email |
| GET/POST | `/v1/users/:id/phone_numbers` | Manage phones |
| POST | `/v1/users/:id/phone_numbers/:id/verify` | Verify phone |

### MFA

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/v1/users/:id/mfa_factors` | List/enroll MFA |
| POST | `/v1/users/:id/mfa_factors/:id/verify` | Verify TOTP |
| POST | `/v1/users/:id/mfa_factors/challenge` | MFA challenge |
| DELETE | `/v1/users/:id/mfa_factors` | Disable MFA |

### Organizations

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/v1/organizations` | List/create orgs |
| GET/PATCH/DELETE | `/v1/organizations/:id` | Get/update/delete org |
| GET/POST | `/v1/organizations/:id/memberships` | Manage members |
| PATCH/DELETE | `/v1/organizations/:id/memberships/:user_id` | Update/remove member |
| GET/POST | `/v1/organizations/:id/invitations` | Manage invitations |
| POST | `/v1/organizations/:id/invitations/accept` | Accept invitation |
| GET/POST | `/v1/organizations/:id/roles` | Custom roles |
| GET/POST | `/v1/organizations/:id/domains` | Domain management |

### Passkeys (WebAuthn)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/passkeys/registration/start` | Start registration |
| POST | `/v1/passkeys/registration/finish` | Finish registration |
| POST | `/v1/passkeys/authentication/start` | Start auth |
| POST | `/v1/passkeys/authentication/finish` | Finish auth |
| GET | `/v1/passkeys` | List passkeys |
| DELETE | `/v1/passkeys/:id` | Delete passkey |

### Webhooks

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/v1/webhooks/endpoints` | CRUD endpoints |
| GET/PATCH/DELETE | `/v1/webhooks/endpoints/:id` | Single endpoint |
| GET | `/v1/webhooks/endpoints/:id/deliveries` | List deliveries |
| POST | `/v1/webhooks/endpoints/:id/deliveries/:id/redeliver` | Retry |

### API Keys

| Method | Path | Scope |
|--------|------|-------|
| GET | `/v1/api_keys` | `gates:api_key:read` |
| POST | `/v1/api_keys` | `gates:api_key:manage` |
| DELETE | `/v1/api_keys/:id` | `gates:api_key:manage` |

### Instance / Config

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/jwks` | Public keys for JWT verification |
| GET | `/v1/jwt_templates` | List JWT templates |
| POST | `/v1/jwt_templates` | Create template |
| GET | `/v1/instance` | Public instance info |
| GET | `/v1/audit_logs` | Paginated audit log |
| GET/POST/DELETE | `/v1/blocklist_identifiers` | Blocklist management |

### OAuth-as-IdP

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/v1/oauth/applications` | Manage OAuth apps |
| GET | `/v1/oauth/authorize` | Authorization endpoint |
| POST | `/v1/oauth/token` | Token exchange |
| GET | `/v1/oauth/userinfo` | Userinfo endpoint |

---

## Webhooks

### Events

Gates fires webhooks for ~28 event types including:

```
user.created         session.created        organization.created
user.updated         session.revoked        organization.updated
user.deleted         session.ended          organization.deleted
email.created        passkey.created        membership.created
email.verified       passkey.deleted        membership.deleted
phone.created        mfaFactor.enabled      invitation.created
phone.verified       mfaFactor.disabled     invitation.accepted
```

### Setting up webhooks

```bash
# 1. Create an endpoint
curl -X POST http://localhost:8000/v1/webhooks/endpoints \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/gates",
    "events": ["user.created", "user.updated", "user.deleted"],
    "enabled": true
  }'

# Response includes a signing secret
# {"id":"...", "secret":"whsec_..."}
```

### Verifying webhook signatures

```python
import hmac, hashlib, time

def verify_webhook(payload: bytes, header: str, secret: str) -> bool:
    """Verify Gates webhook signature."""
    parts = header.split(",")
    if len(parts) < 2:
        return False
    timestamp = int(parts[0][2:])  # t=1234567890
    sig = parts[1][3:]             # v1=hex
    data = str(timestamp).encode() + b"." + payload
    expected = hmac.new(
        secret.encode(), data, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False
    if abs(time.time() - timestamp) > 300:  # 5 min tolerance
        return False
    return True
```

---

## Organizations & RBAC

### System Permissions

Gates includes a built-in permission registry:

| Permission | Description |
|------------|-------------|
| `org:read` | View org details |
| `org:manage` | Update org settings |
| `org:delete` | Delete org |
| `org:create` | Create new orgs |
| `org:member:read` | View members |
| `org:member:manage` | Add/remove members |
| `org:invitation:*` | Manage invitations |
| `user:*` | User management |
| `session:*` | Session management |
| `webhook:*` | Webhook management |
| `api_key:*` | API key management |

### System Roles

| Role | Permissions |
|------|-------------|
| `org:admin` | All `org:*` permissions |
| `org:member` | `org:read`, `org:member:read` |
| `basic_member` | Same as `org:member` |

### API Key Scopes

Server-to-server API keys use `gates:*` scopes:

| Scope | Description |
|-------|-------------|
| `gates:users:read` | Read user data |
| `gates:users:write` | Create/update/delete users |
| `gates:orgs:read` | Read org data |
| `gates:orgs:write` | Manage orgs |
| `gates:*` | Full access (super-admin) |

---

## Deployment

### Docker Compose (Production)

```yaml
services:
  gates:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/gates
      - REDIS_URL=redis://redis:6379/0
      - GATES_FIELD_ENCRYPTION_KEY=${GATES_FIELD_ENCRYPTION_KEY}
      - GATES_JWT_SIGNING_KEY=${GATES_JWT_SIGNING_KEY}
    depends_on: [db, redis]

  db:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
```

### Environment Variables (Production)

```bash
# REQUIRED
GATES_FIELD_ENCRYPTION_KEY=$(openssl rand -base64 32)
GATES_JWT_SIGNING_KEY=$(openssl rand -base64 32)
GATES_PUBLIC_URL=https://auth.yourdomain.com
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/gates
REDIS_URL=redis://host:6379/0
```

### Database Migrations

```bash
uv run alembic upgrade head           # Apply all migrations
uv run alembic downgrade -1           # Rollback one step
uv run alembic history                # View migration history
uv run alembic current                # Current revision
```

---

## Framework Integration Examples

### Vue 3

```vue
<!-- install: npm install @gates/vue -->
<!-- src/main.ts -->
import { createApp } from "vue";
import { createGates } from "@gates/vue";
import App from "./App.vue";

const gates = createGates({ publishableKey: "pk_test_..." });
createApp(App).use(gates).mount("#app");
```

```vue
<!-- src/components/Auth.vue -->
<script setup lang="ts">
import { useAuth, useUser } from "@gates/vue";

const { isSignedIn, signOut, sessionId } = useAuth();
const { user } = useUser();
</script>

<template>
  <div v-if="isSignedIn">
    <p>Welcome, {{ user?.firstName }}</p>
    <button @click="signOut">Sign Out</button>
  </div>
  <div v-else>
    <a href="/sign-in">Sign In</a>
  </div>
</template>
```

```vue
<!-- Router guard -->
<!-- src/router.ts -->
import { createRouter } from "vue-router";
import { gatesAuthGuard } from "@gates/vue";

const routes = [
  {
    path: "/dashboard",
    component: () => import("./views/Dashboard.vue"),
    beforeEnter: gatesAuthGuard(),
  },
];
```

### Nuxt 3

```ts
// plugins/gates.client.ts
import { defineNuxtPlugin } from "#app";
import { createGates } from "@gates/vue";

export default defineNuxtPlugin((nuxtApp) => {
  const gates = createGates({ publishableKey: "pk_test_..." });
  nuxtApp.vueApp.use(gates);
});
```

```ts
// server/middleware/auth.ts
import { defineEventHandler, getCookie, sendRedirect } from "h3";
import jwt from "jsonwebtoken";

export default defineEventHandler((event) => {
  const token = getCookie(event, "__session");
  if (!token) {
    return sendRedirect(event, "/sign-in");
  }
  try {
    const payload = jwt.verify(token, process.env.GATES_JWT_KEY!);
    event.context.auth = payload;
  } catch {
    return sendRedirect(event, "/sign-in");
  }
});
```

```vue
<!-- composables/useGatesUser.ts -->
import { useState } from "#app";

export const useGatesUser = () => {
  return useState("gates-user", () => null);
};
```

### Express.js (Node.js Backend)

```bash
npm install @gates/server-node jsonwebtoken cookie-parser
```

```js
// middleware/auth.js
const jwt = require("jsonwebtoken");

function gatesAuth(req, res, next) {
  const token = req.cookies?.__session || req.headers.authorization?.replace("Bearer ", "");

  if (!token) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  try {
    const payload = jwt.verify(token, process.env.GATES_JWT_KEY);
    req.user = { id: payload.sub, sessionId: payload.sid };
    req.session = payload;
    next();
  } catch (err) {
    return res.status(401).json({ error: "Invalid token" });
  }
}

// requireOrgRole middleware
function requireOrgRole(role) {
  return (req, res, next) => {
    if (req.session?.org_role !== role) {
      return res.status(403).json({ error: "Forbidden" });
    }
    next();
  };
}

module.exports = { gatesAuth, requireOrgRole };
```

```js
// app.js
const express = require("express");
const cookieParser = require("cookie-parser");
const { gatesAuth, requireOrgRole } = require("./middleware/auth");

const app = express();
app.use(cookieParser());

app.get("/me", gatesAuth, (req, res) => {
  res.json({ user: req.user });
});

app.post("/admin", gatesAuth, requireOrgRole("org:admin"), (req, res) => {
  res.json({ secret: "admin-only data" });
});
```

### FastAPI (Python Backend — native)

```python
# app.py
from fastapi import FastAPI, Depends, Request
from gates_server import gates, require_auth, require_permission

app = FastAPI()

@gates()
@app.get("/me")
@require_auth
async def my_profile(request: Request):
    user = request.state.gates.user()
    return {"id": user.id, "email": user.email, "username": user.username}

@gates()
@app.get("/users")
@require_auth
@require_permission("gates:users:read")
async def list_users(request: Request):
    # Access the Gates admin API directly
    client = request.state.gates.client()
    users = await client.users.list()
    return {"data": users}

# Or without the SDK — just verify the JWT manually

def verify_gates_token(request: Request):
    token = request.cookies.get("__session")
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        raise HTTPException(401, "Unauthorized")
    try:
        payload = jwt.decode(
            token,
            settings.GATES_JWT_SIGNING_KEY,
            algorithms=["HS256"],
        )
        request.state.user_id = payload["sub"]
        request.state.session_id = payload["sid"]
    except Exception:
        raise HTTPException(401, "Invalid token")

@app.get("/protected")
async def protected_route(request: Request, _=Depends(verify_gates_token)):
    return {"user_id": request.state.user_id}
```

### Remix

```tsx
// app/root.tsx
import { GatesProvider } from "@gates/react";
import { Links, Meta, Outlet } from "@remix-run/react";

export default function Root() {
  return (
    <html>
      <head><Meta /><Links /></head>
      <body>
        <GatesProvider publishableKey="pk_test_...">
          <Outlet />
        </GatesProvider>
      </body>
    </html>
  );
}
```

```tsx
// app/routes/dashboard.tsx
import { json, LoaderFunctionArgs, redirect } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";

export async function loader({ request }: LoaderFunctionArgs) {
  const cookieHeader = request.headers.get("Cookie") || "";
  const token = cookieHeader
    .split(";")
    .find((c) => c.trim().startsWith("__session="))
    ?.split("=")[1];

  if (!token) return redirect("/sign-in");

  try {
    const jwt = require("jsonwebtoken");
    const payload = jwt.verify(token, process.env.GATES_JWT_KEY!);
    return json({ userId: payload.sub, email: payload.email });
  } catch {
    return redirect("/sign-in");
  }
}

export default function Dashboard() {
  const { userId, email } = useLoaderData<typeof loader>();
  return <h1>Welcome {email} (ID: {userId})</h1>;
}
```

### SvelteKit

```ts
// src/hooks.server.ts
import type { Handle } from "@sveltejs/kit";
import jwt from "jsonwebtoken";

export const handle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get("__session");

  if (token) {
    try {
      const payload = jwt.verify(token, process.env.GATES_JWT_KEY!);
      event.locals.user = { id: payload.sub, sessionId: payload.sid };
      event.locals.session = payload;
    } catch {
      // Token invalid — leave unauthenticated
    }
  }

  return resolve(event);
};
```

```ts
// src/routes/dashboard/+page.server.ts
import { redirect } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) {
    throw redirect(302, "/sign-in");
  }
  return { user: locals.user };
};
```

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import { GatesProvider } from "@gates/react";
  import { browser } from "$app/environment";
</script>

<svelte:head>
  {#if browser}
    <script src="https://cdn.tailwindcss.com"></script>
  {/if}
</svelte:head>

<GatesProvider publishableKey="pk_test_...">
  <slot />
</GatesProvider>
```

---

## FAQ & Troubleshooting

### "How do I reset the admin password?"

Use the hosted forgot-password flow at `/forgot-password` or call:
```bash
curl -X POST /v1/passwords/reset -d '{"email":"admin@example.com"}'
```

### "How do I get the user's session on the server?"

The JWT is in the `__session` cookie. Decode it:
```python
import jwt
token = request.cookies.get("__session")
payload = jwt.decode(token, options={"verify_signature": False})
user_id = payload["sub"]
```

### "My session keeps expiring"

JWT tokens expire after 60 minutes. The SDK auto-refreshes using the `__session_refresh` cookie. Ensure your frontend makes a request to `POST /v1/tokens` before the 60-min window expires.

### "How do I disable 2FA for a user?"

```bash
curl -X DELETE http://localhost:8000/v1/users/:id/mfa_factors \
  -H "Authorization: Bearer <admin-token>"
```

### "Database migration fails"

Ensure PostgreSQL is running and the `DATABASE_URL` in `.env` is correct:
```bash
docker compose up -d postgres
uv run alembic upgrade head
```

### "How do I customize JWT claims?"

Create a JWT template:
```bash
curl -X POST /v1/jwt_templates \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "custom",
    "claims": {"org_id": "{{user.organization_id}}"}
  }'
```

---

## Hosted Pages

When you don't want to build your own UI, Gates provides hosted pages:

| URL | Description |
|-----|-------------|
| `/sign-in` | Sign in form |
| `/sign-up` | Registration form |
| `/forgot-password` | Password reset request |
| `/verify` | Email/phone verification |
| `/user/profile` | Account details |
| `/user/security` | Security settings |

These pages are served by the Gates backend using Jinja2 templates and are fully customizable.

---

## Need Help?

- Open an issue at [github.com/anomalyco/opencode/issues](https://github.com/anomalyco/opencode/issues)
- Review the full OpenAPI spec at `http://localhost:8000/docs`
- Check `AGENTS.md` for the complete feature specification
