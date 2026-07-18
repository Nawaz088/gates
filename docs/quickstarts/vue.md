# Vue 3 Quickstart

## Installation

```bash
npm install @gates/vue
```

## Setup

```ts
// main.ts
import { createApp } from "vue";
import { createGates } from "@gates/vue";
import App from "./App.vue";

const gates = createGates({ publishableKey: "pk_test_..." });
createApp(App).use(gates).mount("#app");
```

## Composables

```vue
<script setup lang="ts">
import { useAuth, useUser } from "@gates/vue";

const { isSignedIn, signOut, sessionId } = useAuth();
const { user } = useUser();
</script>

<template>
  <div v-if="isSignedIn">
    <p>Welcome, {{ user?.firstName }}</p>
    <p>Session: {{ sessionId }}</p>
    <button @click="signOut">Sign Out</button>
  </div>
  <div v-else>
    <a href="/sign-in">Sign In</a>
  </div>
</template>
```

## Router Guard

```ts
import { createRouter } from "vue-router";
import { gatesAuthGuard } from "@gates/vue";

const router = createRouter({
  routes: [
    {
      path: "/dashboard",
      component: () => import("./views/Dashboard.vue"),
      beforeEnter: [gatesAuthGuard()],
    },
  ],
});
```
