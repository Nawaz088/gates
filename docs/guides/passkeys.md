# Passkeys (WebAuthn)

## Overview

Passkeys allow users to sign in with biometrics (fingerprint, face) or platform authenticators (Windows Hello, Touch ID, Android biometrics).

## Registration Flow

```javascript
// 1. Start registration — get challenge from server
const startResp = await fetch("/v1/passkeys/registration/start", {
  headers: { Authorization: "Bearer <session>" },
});
const options = await startResp.json();

// 2. Create credential via browser API
const credential = await navigator.credentials.create({
  publicKey: {
    challenge: Uint8Array.from(options.challenge, c => c.charCodeAt(0)),
    rp: { id: options.rpId, name: options.rpName },
    user: {
      id: Uint8Array.from(options.userId, c => c.charCodeAt(0)),
      name: options.userName,
      displayName: options.userName,
    },
    pubKeyCredParams: options.pubkeyCredParams,
    timeout: options.timeout,
    excludeCredentials: options.excludeCredentials,
    authenticatorSelection: options.authenticatorSelection,
  },
});

// 3. Send credential to server to verify
await fetch("/v1/passkeys/registration/finish", {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: "Bearer <session>" },
  body: JSON.stringify({ credential, name: "My Passkey" }),
});
```

## Authentication Flow

```javascript
// 1. Start authentication
const startResp = await fetch("/v1/passkeys/authentication/start", {
  headers: { Authorization: "Bearer <session>" },
});
const options = await startResp.json();

// 2. Get assertion from browser
const assertion = await navigator.credentials.get({
  publicKey: {
    challenge: Uint8Array.from(options.challenge, c => c.charCodeAt(0)),
    rpId: options.rpId,
    allowCredentials: options.allowCredentials,
    timeout: options.timeout,
    userVerification: options.userVerification,
  },
});

// 3. Verify assertion
await fetch("/v1/passkeys/authentication/finish", {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: "Bearer <session>" },
  body: JSON.stringify({ credential: assertion }),
});
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/passkeys/registration/start` | Get registration options |
| POST | `/v1/passkeys/registration/finish` | Verify and store credential |
| POST | `/v1/passkeys/authentication/start` | Get authentication options |
| POST | `/v1/passkeys/authentication/finish` | Verify assertion |
| GET | `/v1/passkeys` | List user's passkeys |
| DELETE | `/v1/passkeys/:id` | Delete a passkey |

## Security

- Challenges are 32 random bytes, single-use, 5 min TTL
- ResidentKey (`discoverable credentials`) required
- User verification required
- Sign count tracked for replay protection
- Backup-eligible state tracked per credential
