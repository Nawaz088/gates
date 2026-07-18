# React Quickstart

## Installation

```bash
npm install @gates/react
# or
pnpm add @gates/react
```

## Setup

Wrap your app with `<GatesProvider>`:

```tsx
import { GatesProvider } from "@gates/react";

function App() {
  return (
    <GatesProvider publishableKey="pk_test_...">
      <YourApp />
    </GatesProvider>
  );
}
```

## Hooks

```tsx
import { useAuth, useUser, useSession } from "@gates/react";

function Profile() {
  const { isSignedIn, isLoaded, signOut } = useAuth();
  const { user } = useUser();
  const { session } = useSession();

  if (!isLoaded) return <div>Loading...</div>;
  if (!isSignedIn) return <a href="/sign-in">Sign In</a>;

  return (
    <div>
      <h1>Hello, {user?.firstName}</h1>
      <p>Session: {session?.id}</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  );
}
```

## Components

```tsx
import { SignedIn, SignedOut, SignIn, SignUp, UserButton, UserProfile, Protect } from "@gates/react";

function Nav() {
  return (
    <nav>
      <SignedIn>
        <UserButton />
      </SignedIn>
      <SignedOut>
        <a href="/sign-in">Sign In</a>
        <a href="/sign-up">Sign Up</a>
      </SignedOut>

      <Protect role="org:admin">
        <a href="/admin">Admin Panel</a>
      </Protect>
    </nav>
  );
}

function AuthPage() {
  return (
    <div>
      <SignIn afterSignInUrl="/dashboard" signUpUrl="/sign-up" />
    </div>
  );
}

function SettingsPage() {
  return <UserProfile />;
}
```

## Vite Proxy Configuration

```ts
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      "/v1": "http://localhost:8000",
      "/__session": "http://localhost:8000",
    },
  },
});
```
