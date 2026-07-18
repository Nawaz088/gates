# Gates Documentation

> A self-hostable, full-featured authentication and user-management platform.

---

## Quickstarts

### Frontend

- [React (Vite)](quickstarts/react.md) — `@gates/react`
- [Next.js](quickstarts/nextjs.md) — `@gates/nextjs`
- [Vue 3](quickstarts/vue.md) — `@gates/vue`
- [Nuxt 3](quickstarts/nuxt.md) — `@gates/nuxt`
- [Remix](quickstarts/remix.md) — `@gates/remix`
- [SvelteKit](quickstarts/sveltekit.md) — `@gates/sveltekit`

### Backend

- [Python / FastAPI](quickstarts/python.md) — `@gates/server-python`
- [Node.js / Express](quickstarts/express.md) — `@gates/server-node`
- [Ruby on Rails](quickstarts/rails.md)
- [Go](quickstarts/go.md)

### Mobile

- [React Native / Expo](quickstarts/expo.md)

---

## Features

### Authentication

- [Email + Password](guides/email-password.md)
- [Magic Link](guides/magic-link.md)
- [OTP Codes (Email/SMS)](guides/otp.md)
- [Social OAuth](guides/oauth.md) — Google, GitHub, Apple, Microsoft
- [Passkeys / WebAuthn](guides/passkeys.md)
- [SAML SSO](guides/saml.md)
- [OIDC SSO](guides/oidc.md)
- [Multi-Factor Authentication](guides/mfa.md)
- [Impersonation](guides/impersonation.md)
- [Anonymous Users](guides/anonymous.md)

### User Management

- [Managing Users](guides/users.md)
- [Email & Phone Numbers](guides/emails-phones.md)
- [Sessions & Tokens](guides/sessions.md)
- [Account Linking](guides/account-linking.md)

### Organizations

- [Organizations Overview](guides/organizations.md)
- [Members & Roles](guides/members-roles.md)
- [Invitations](guides/invitations.md)
- [Domain Verification](guides/domain-verification.md)

### Security

- [API Keys](guides/api-keys.md)
- [Webhooks](guides/webhooks.md)
- [Rate Limiting](security/rate-limiting.md)
- [Bot Protection](security/bot-protection.md)
- [Blocklist](security/blocklist.md)
- [Audit Logs](security/audit-logs.md)
- [GDPR & Data Export](security/gdpr.md)

### Configuration

- [Instance Settings](guides/instance.md)
- [JWT Templates](guides/jwt-templates.md)
- [Email Templates](guides/email-templates.md)
- [Environment Variables](guides/environment.md)

---

## SDK Reference

- [@gates/react](sdks/react.md) — Hooks, components, provider
- [@gates/nextjs](sdks/nextjs.md) — Server helpers, middleware
- [@gates/vue](sdks/vue.md) — Composables, plugin
- [@gates/server-python](sdks/server-python.md) — FastAPI integration
- [@gates/server-node](sdks/server-node.md) — Express middleware

---

## API Reference

Full REST API under `/v1/*`. OpenAPI spec at `http://localhost:8000/docs`.

- [Authentication Endpoints](reference/auth.md)
- [User Endpoints](reference/users.md)
- [Session Endpoints](reference/sessions.md)
- [Organization Endpoints](reference/organizations.md)
- [Webhook Endpoints](reference/webhooks.md)
- [API Key Endpoints](reference/api-keys.md)

---

## Concepts

- [How Gates Works](concepts/how-it-works.md)
- [Session & Token Lifecycle](concepts/sessions.md)
- [JWT Claims](concepts/jwt-claims.md)
- [Permission Model](concepts/permissions.md)
- [Multi-Tenancy](concepts/multi-tenancy.md)

---

## Deployment

- [Docker Compose](deployment/docker.md)
- [Environment Variables](deployment/env.md)
- [Database Migrations](deployment/migrations.md)
- [Production Checklist](deployment/production.md)

---

## Need Help?

- GitHub Issues: [github.com/anomalyco/opencode/issues](https://github.com/anomalyco/opencode/issues)
- API Docs: `http://localhost:8000/docs`
