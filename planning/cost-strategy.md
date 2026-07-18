# Gates Cost Strategy

## Why Auth Providers Are Expensive

| Provider | Pricing | 1K MAU | 10K MAU | 100K MAU |
|----------|--------|--------|---------|----------|
| Clerk | $0.049/MAU + tiers | ~$49/mo | ~$490/mo | ~$4,900/mo |
| Auth0 | 7.5K free then $0.023/MAU | Free | ~$58/mo | ~$2,300/mo |
| Supabase Auth | Included in DB plan | $0 | $25/mo | $500/mo |
| Firebase Auth | Free under limits | $0 | $25/mo | ~$450/mo |
| **Gates** | **Self-hosted infra only** | **~$5-10/mo** | **~$10-20/mo** | **~$50-100/mo** |

## Strategy

Self-hosted only. Zero per-user fees. All features unlocked.

## Feature Price Comparison

| Feature | Clerk Price | Gates Price |
|---------|------------|-------------|
| Email/Password | Free | Free |
| Social OAuth | Free | Free |
| Organizations | $25/mo (Pro) | Free |
| MFA / TOTP | $25/mo (Pro) | Free |
| SAML / OIDC SSO | $99/mo (Enterprise) | Free |
| Passkeys / WebAuthn | Free | Free |
| Webhooks | Free | Free |
| JWT Templates | Free | Free |
| API Keys | Free | Free |
| Audit Logs | $25/mo (Pro) | Free |
| **10K users/mo** | **~$490/mo** | **~$10-20/mo** |

## Infrastructure Cost Guide

| Scale | Users | VPS | Database | Total |
|-------|-------|-----|----------|-------|
| Hobby | < 1K | $5 (2GB) | Free (SQLite) | **$5/mo** |
| Startup | < 10K | $12 (4GB) | $15 (managed PG) | **$27/mo** |
| Growing | < 100K | $30 (8GB) | $50 (managed PG) | **$80/mo** |
| Scale | < 1M | $60+ (16GB) | $200+ (PG cluster) | **$260/mo** |

## Monetization (No Per-User Fees)

| Stream | Description | Target Price |
|--------|-------------|-------------|
| Managed Hosting | We host their instance | $29-299/mo |
| Support Contracts | SLA-backed support | $99-999/mo |
| Enterprise Add-ons | Audit, compliance reports | $199-499/mo |
| Consulting | Migration, custom integration | $500-5K one-time |

## Go-To-Market Angles

1. "Clerk costs $490/mo for 10K users. Gates costs $27/mo."
2. "All features included. No tiers."
3. "Self-hosted. Your data, your servers."
4. "Unlimited API keys, webhooks, audit logs."

## Implementation Checklist

- [ ] Pricing comparison page in docs
- [ ] One-click deploy templates (Fly.io, Railway, Render)
- [ ] SQLite support for hobby tier
- [ ] Migration guides from Clerk/Auth0
- [ ] Cost calculator in docs
