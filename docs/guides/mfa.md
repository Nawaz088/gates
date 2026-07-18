# Multi-Factor Authentication

Gates supports TOTP-based MFA with backup codes.

## Enabling TOTP

```bash
# 1. Enroll — returns provisioning URI for QR code
curl -X POST http://localhost:8000/v1/users/:id/mfa_factors \
  -H "Authorization: Bearer <token>"

# Response:
{
  "factorId": "mfa_cuid123",
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioningUri": "otpauth://totp/Gates:user@example.com?secret=..."
}

# 2. Verify — scan QR with authenticator app, submit code
curl -X POST http://localhost:8000/v1/users/:id/mfa_factors/:factor_id/verify \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'

# Response includes 10 backup codes:
{
  "status": "verified",
  "backupCodes": ["a1b2c3d4", "e5f6g7h8", ...]
}
```

## Sign-In with MFA

```
POST /v1/sign_ins (password correct)
  → 200 { status: "needs_mfa" }
  → User prompted for TOTP code

POST /v1/users/:id/mfa_factors/challenge
  -d '{"code": "123456"}'
  → 200 { status: "verified" }
  → Session issued
```

## Backup Codes

- 10 codes generated on TOTP verification
- Each code is single-use
- Displayed once — user must save them
- Stored as SHA256 hashes

```bash
# Use backup code instead of TOTP:
curl -X POST /v1/users/:id/mfa_factors/challenge \
  -d '{"code": "a1b2c3d4"}'
# → 200 { "status": "verified", "method": "backup_code" }
```

## Disabling MFA

```bash
curl -X DELETE http://localhost:8000/v1/users/:id/mfa_factors \
  -H "Authorization: Bearer <token>"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/users/:id/mfa_factors` | List enrolled factors |
| POST | `/v1/users/:id/mfa_factors` | Enroll TOTP |
| POST | `/v1/users/:id/mfa_factors/:factor_id/verify` | Verify TOTP + generate backup codes |
| POST | `/v1/users/:id/mfa_factors/challenge` | Verify during sign-in |
| DELETE | `/v1/users/:id/mfa_factors` | Disable all MFA |
