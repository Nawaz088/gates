# Express.js Quickstart

## Installation

```bash
npm install @gates/server-node jsonwebtoken cookie-parser
```

## Setup

```js
const express = require("express");
const cookieParser = require("cookie-parser");
const { GatesClient, requireAuth } = require("@gates/server-node");

const app = express();
app.use(cookieParser());

const gates = new GatesClient({
  jwtKey: process.env.GATES_JWT_KEY,
  secretKey: process.env.GATES_SECRET_KEY, // for admin API calls
});

// Protected route
app.get("/me", requireAuth(gates), async (req, res) => {
  const user = await gates.users.getUser(req.auth.userId);
  res.json({ user });
});

// Role-based access
app.post("/admin", requireAuth(gates, { orgRole: "org:admin" }), (req, res) => {
  res.json({ secret: "admin-only" });
});

// Admin API call with secret key
app.get("/api/users", async (req, res) => {
  const users = await gates.users.list();
  res.json(users);
});
```

## Manual JWT Verification

```js
const jwt = require("jsonwebtoken");

function gatesAuth(req, res, next) {
  const token = req.cookies?.__session ||
    req.headers.authorization?.replace("Bearer ", "");

  if (!token) return res.status(401).json({ error: "Unauthorized" });

  try {
    const payload = jwt.verify(token, process.env.GATES_JWT_KEY);
    req.user = { id: payload.sub, sessionId: payload.sid };
    req.orgRole = payload.org_role;
    next();
  } catch {
    return res.status(401).json({ error: "Invalid token" });
  }
}
```
