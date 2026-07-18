# API Keys

API keys allow server-to-server authentication without a user session.

## Creating an API Key

```bash
curl -X POST http://localhost:8000/v1/api_keys \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "scopes": ["gates:users:read", "gates:orgs:read"]
  }'

# Response:
{
  "id": "key_cuid123",
  "name": "CI/CD Pipeline",
  "keyPrefix": "gates_ab12",
  "key": "gates_ab12cd34ef56gh78ij90kl12mn34op56qr78st90uv12wx34yz",
  "scopes": ["gates:users:read", "gates:orgs:read"]
}
```

The full key is shown only once. Store it securely.

## Using an API Key

```bash
curl http://localhost:8000/v1/users \
  -H "Authorization: Bearer gates_ab12cd34ef56gh78ij90kl12mn34op56qr78st90uv12wx34yz"
```

## Available Scopes

| Scope | Description |
|-------|-------------|
| `gates:users:read` | Read user data |
| `gates:users:write` | Create, update, delete users |
| `gates:users:ban` | Ban/unban users |
| `gates:orgs:read` | Read organization data |
| `gates:orgs:write` | Create, update, delete orgs |
| `gates:orgs:members:read` | Read memberships |
| `gates:orgs:members:write` | Manage members |
| `gates:session:read` | Read sessions |
| `gates:session:revoke` | Revoke sessions |
| `gates:webhook:read` | Read webhook endpoints |
| `gates:webhook:manage` | Create, update, delete webhooks |
| `gates:api_key:read` | List API keys |
| `gates:api_key:manage` | Create, revoke API keys |
| `gates:*` | **Full access** (super-admin only) |

## Revoking an API Key

```bash
curl -X DELETE http://localhost:8000/v1/api_keys/:id \
  -H "Authorization: Bearer <admin-token>"
```

## API Endpoints

| Method | Path | Required Scope |
|--------|------|----------------|
| GET | `/v1/api_keys` | `gates:api_key:read` |
| POST | `/v1/api_keys` | `gates:api_key:manage` |
| GET | `/v1/api_keys/:id` | `gates:api_key:read` |
| DELETE | `/v1/api_keys/:id` | `gates:api_key:manage` |
