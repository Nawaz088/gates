# Social OAuth

Gates supports social sign-in via Google, GitHub, Apple, and Microsoft.

## How It Works

```
1. User clicks "Sign in with Google"
2. GET /v1/oauth/authorize?provider=google&redirect=/dashboard
3. Redirects to Google consent screen
4. User authorizes → Google redirects to callback URL
5. GET /v1/oauth/callback/google?code=...
6. Server exchanges code for tokens, fetches user info
7. Creates or links user account, issues session
8. Redirects back to your app with session cookies
```

## Configuration

Set provider credentials via environment variables or instance config:

```env
# Google
GATES_GOOGLE_CLIENT_ID=...
GATES_GOOGLE_CLIENT_SECRET=...

# GitHub
GATES_GITHUB_CLIENT_ID=...
GATES_GITHUB_CLIENT_SECRET=...

# Apple
GATES_APPLE_CLIENT_ID=...
GATES_APPLE_CLIENT_SECRET=...

# Microsoft
GATES_MICROSOFT_CLIENT_ID=...
GATES_MICROSOFT_CLIENT_SECRET=...
```

## Provider Details

| Provider | Userinfo Fields |
|----------|----------------|
| Google | `sub`, `email`, `given_name`, `family_name`, `picture` |
| GitHub | `id`, `email`, `name`, `avatar_url` |
| Apple | `sub`, `email`, `given_name`, `family_name` (from id_token) |
| Microsoft | `id`, `mail`, `givenName`, `surname` |

## Account Linking

When a user signs in with a social provider that has the same email as an existing account:

1. If they have an existing `external_account` for the same provider → instant sign-in
2. If they have an existing account with the same email from a different provider → account linking required
3. If no existing account → new user + external_account created

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/oauth/authorize` | Initiate OAuth flow |
| GET | `/v1/oauth/callback/:provider` | Handle OAuth callback |
