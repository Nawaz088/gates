# Managing Users

## User Object

```json
{
  "id": "user_cuid123",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "username": "johndoe",
  "imageUrl": "https://...",
  "banned": false,
  "twoFactorEnabled": true,
  "publicMetadata": {},
  "unsafeMetadata": {},
  "lastSignInAt": "2025-07-18T12:00:00Z",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/users` | List users (paginated) |
| POST | `/v1/users` | Create user |
| GET | `/v1/users/:id` | Get user |
| PATCH | `/v1/users/:id` | Update user |
| DELETE | `/v1/users/:id` | Delete user |
| POST | `/v1/users/:id/ban` | Ban user |
| POST | `/v1/users/:id/unban` | Unban user |
| POST | `/v1/users/:id/lock` | Lock account |
| POST | `/v1/users/:id/unlock` | Unlock account |
| POST | `/v1/users/:id/impersonate` | Impersonate user |

## Metadata

Users have three metadata fields:

| Field | Writable By | Readable By |
|-------|-------------|-------------|
| `publicMetadata` | Admin API | User + Admin |
| `privateMetadata` | Admin API | Admin only (can hold PII) |
| `unsafeMetadata` | Client SDK | User + Admin |

## Ban vs Lock

| Action | Effect | Duration |
|--------|--------|----------|
| **Ban** | Prevents all sign-in | Permanent (until unbanned) |
| **Lock** | Prevents sign-in after failed attempts | 30 min (configurable) |
