# Organizations

## Overview

Organizations are shared accounts for team collaboration. Members can have different roles with varying permission levels.

## Create an Organization

```bash
curl -X POST http://localhost:8000/v1/organizations \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "slug": "acme-corp",
    "maxMembers": 50
  }'
```

## Manage Members

```bash
# List members
curl http://localhost:8000/v1/organizations/:id/memberships \
  -H "Authorization: Bearer <token>"

# Add member
curl -X POST http://localhost:8000/v1/organizations/:id/memberships \
  -H "Authorization: Bearer <token>" \
  -d '{"userId": "user_cuid123", "role": "basic_member"}'

# Update role
curl -X PATCH http://localhost:8000/v1/organizations/:id/memberships/:user_id \
  -H "Authorization: Bearer <token>" \
  -d '{"role": "org:admin"}'

# Remove member
curl -X DELETE http://localhost:8000/v1/organizations/:id/memberships/:user_id \
  -H "Authorization: Bearer <token>"
```

## Invitations

```bash
# Invite by email
curl -X POST http://localhost:8000/v1/organizations/:id/invitations \
  -H "Authorization: Bearer <token>" \
  -d '{"email": "user@example.com", "role": "basic_member"}'

# Accept invitation (user must be signed in)
curl -X POST http://localhost:8000/v1/organizations/:id/invitations/accept \
  -H "Authorization: Bearer <token>" \
  -d '{"token": "invite_token_here"}'

# Revoke invitation
curl -X POST http://localhost:8000/v1/organizations/:id/invitations/:inv_id/revoke \
  -H "Authorization: Bearer <token>"
```

## Custom Roles

```bash
curl -X POST http://localhost:8000/v1/organizations/:id/roles \
  -H "Authorization: Bearer <token>" \
  -d '{
    "key": "viewer",
    "name": "Viewer",
    "permissions": ["org:read", "org:member:read"],
    "description": "Read-only access"
  }'
```

## Domain Verification

```bash
# Add domain
curl -X POST http://localhost:8000/v1/organizations/:id/domains \
  -H "Authorization: Bearer <token>" \
  -d '{"domain": "example.com", "enrollmentMode": "automatic"}'

# Verify domain (add TXT record with returned token)
curl -X POST http://localhost:8000/v1/organizations/:id/domains/:domain_id/verify \
  -H "Authorization: Bearer <token>" \
  -d '{"token": "verification_token"}'
```

## Active Organization

Set the active org via header `X-Gates-Organization-Id`. This scopes the JWT claims:

```json
{
  "sub": "user_cuid123",
  "org_id": "org_cuid456",
  "org_role": "org:admin",
  "org_permissions": ["org:read", "org:write"]
}
```

## API Endpoints

| Method | Path |
|--------|------|
| GET/POST | `/v1/organizations` |
| GET/PATCH/DELETE | `/v1/organizations/:id` |
| GET/POST | `/v1/organizations/:id/memberships` |
| PATCH/DELETE | `/v1/organizations/:id/memberships/:user_id` |
| GET/POST | `/v1/organizations/:id/invitations` |
| POST | `/v1/organizations/:id/invitations/accept` |
| POST | `/v1/organizations/:id/invitations/:inv_id/revoke` |
| GET/POST | `/v1/organizations/:id/roles` |
| GET/POST | `/v1/organizations/:id/domains` |
