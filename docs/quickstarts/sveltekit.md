# SvelteKit Quickstart

## Installation

```bash
npm install @gates/sveltekit @gates/react
```

## Hooks

```ts
// src/hooks.server.ts
import type { Handle } from "@sveltejs/kit";
import jwt from "jsonwebtoken";

export const handle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get("__session");

  if (token) {
    try {
      const payload = jwt.verify(token, process.env.GATES_JWT_KEY!);
      event.locals.user = { id: payload.sub, sessionId: payload.sid };
      event.locals.session = payload;
    } catch {
      // invalid token, leave unauthenticated
    }
  }

  return resolve(event);
};
```

## Page Protection

```ts
// src/routes/dashboard/+page.server.ts
import { redirect } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) throw redirect(302, "/sign-in");
  return { user: locals.user };
};
```

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import { GatesProvider } from "@gates/react";
  import { browser } from "$app/environment";
</script>

<GatesProvider publishableKey="pk_test_...">
  <slot />
</GatesProvider>
```

## Client-Side Auth

```svelte
<script lang="ts">
  import { useAuth, useUser } from "@gates/react";
  const { isSignedIn, signOut } = useAuth();
  const { user } = useUser();
</script>

{#if $isSignedIn}
  <p>Hello {$user?.firstName}</p>
  <button on:click={signOut}>Sign Out</button>
{:else}
  <a href="/sign-in">Sign In</a>
{/if}
```
