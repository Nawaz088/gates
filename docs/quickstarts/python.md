# Python / FastAPI Quickstart

## Installation

```bash
pip install @gates/server-python
# or
uv add @gates/server-python
```

## Setup

```python
from fastapi import FastAPI, Request
from gates_server import gates, require_auth, require_org_role, require_permission

app = FastAPI()

@gates(
    jwt_key="your-gates-jwt-signing-key",  # or set GATES_JWT_KEY env
    jwks_url="http://localhost:8000/v1/jwks",
)
@app.get("/me")
@require_auth
async def my_profile(request: Request):
    user = request.state.gates.user()
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "session": request.state.gates.session(),
    }

@app.get("/admin")
@require_auth
@require_org_role("org:admin")
async def admin_only(request: Request):
    return {"secret": "admin-data"}

@app.get("/api/users")
@require_auth
@require_permission("gates:users:read")
async def list_users(request: Request):
    client = request.state.gates.client()
    users = await client.users.list()
    return {"data": users}
```

## Manual JWT Verification

```python
from fastapi import Depends, HTTPException, Request
import jwt
from gates.config import settings

async def verify_gates_token(request: Request):
    token = request.cookies.get("__session")
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]

    if not token:
        raise HTTPException(401, "Unauthorized")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_signing_key,
            algorithms=["HS256"],
        )
        request.state.user_id = payload["sub"]
        request.state.session_id = payload["sid"]
        request.state.org_role = payload.get("org_role")
        return payload
    except Exception:
        raise HTTPException(401, "Invalid token")

@app.get("/protected")
async def protected(_=Depends(verify_gates_token)):
    return {"status": "authenticated"}
```
