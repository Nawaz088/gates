# Next.js Quickstart

## Installation

```bash
npm install @gates/nextjs @gates/react
```

## App Router — Provider

```tsx
// app/layout.tsx
import { GatesProvider } from "@gates/react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <GatesProvider publishableKey="pk_test_...">
          {children}
        </GatesProvider>
      </body>
    </html>
  );
}
```

## App Router — Server Components

```tsx
// app/page.tsx
import { auth, currentUser } from "@gates/nextjs";

export default async function Home() {
  const { userId, isSignedIn, orgRole } = await auth();
  const user = await currentUser();

  return (
    <div>
      {isSignedIn ? (
        <p>Welcome back, {user?.email || userId}</p>
      ) : (
        <p>Please sign in</p>
      )}
    </div>
  );
}
```

## App Router — Middleware

```ts
// middleware.ts
import { auth, createRouteMatcher } from "@gates/nextjs";
import { NextResponse } from "next/server";

const protectedRoutes = createRouteMatcher(["/dashboard(.*)", "/admin(.*)"]);

export default async function middleware(req: Request) {
  const { isSignedIn } = await auth();
  const path = new URL(req.url).pathname;

  if (protectedRoutes(path) && !isSignedIn) {
    return NextResponse.redirect(new URL("/sign-in", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|sign-in|sign-up|api/auth).*)"],
};
```

## API Routes

```ts
// app/api/protected/route.ts
import { auth } from "@gates/nextjs";
import { NextResponse } from "next/server";

export async function GET() {
  const { userId, isSignedIn } = await auth();
  if (!isSignedIn) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return NextResponse.json({ userId });
}
```
