# Nuxt 3 Quickstart

## Installation

```bash
npm install @gates/vue
```

## Plugin

```ts
// plugins/gates.client.ts
import { defineNuxtPlugin } from "#app";
import { createGates } from "@gates/vue";

export default defineNuxtPlugin((nuxtApp) => {
  const gates = createGates({ publishableKey: "pk_test_..." });
  nuxtApp.vueApp.use(gates);
});
```

## Composables

```vue
<script setup lang="ts">
const { isSignedIn, user, signOut } = useAuth();
</script>

<template>
  <div>
    <p v-if="isSignedIn">Welcome, {{ user?.firstName }}</p>
    <button v-if="isSignedIn" @click="signOut">Sign Out</button>
    <a v-else href="/sign-in">Sign In</a>
  </div>
</template>
```

## Server Middleware

```ts
// server/middleware/auth.ts
import { defineEventHandler, getCookie, sendRedirect } from "h3";
import jwt from "jsonwebtoken";

export default defineEventHandler((event) => {
  const token = getCookie(event, "__session");
  if (!token) return sendRedirect(event, "/sign-in");

  try {
    const payload = jwt.verify(token, process.env.GATES_JWT_KEY!);
    event.context.auth = payload;
  } catch {
    return sendRedirect(event, "/sign-in");
  }
});
```
