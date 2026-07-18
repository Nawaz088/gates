# Remix Quickstart

## Installation

```bash
npm install @gates/react
```

## Setup

```tsx
// app/root.tsx
import { GatesProvider } from "@gates/react";
import { Links, Meta, Outlet } from "@remix-run/react";

export default function Root() {
  return (
    <html>
      <head><Meta /><Links /></head>
      <body>
        <GatesProvider publishableKey="pk_test_...">
          <Outlet />
        </GatesProvider>
      </body>
    </html>
  );
}
```

## Loader Auth

```tsx
// app/routes/dashboard.tsx
import { json, LoaderFunctionArgs, redirect } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import jwt from "jsonwebtoken";

export async function loader({ request }: LoaderFunctionArgs) {
  const cookieHeader = request.headers.get("Cookie") || "";
  const token = cookieHeader
    .split(";")
    .find((c) => c.trim().startsWith("__session="))
    ?.split("=")[1];

  if (!token) return redirect("/sign-in");

  try {
    const payload = jwt.verify(token, process.env.GATES_JWT_KEY!);
    return json({ userId: payload.sub, email: payload.email });
  } catch {
    return redirect("/sign-in");
  }
}

export default function Dashboard() {
  const { userId, email } = useLoaderData<typeof loader>();
  return <h1>Welcome {email}</h1>;
}
```

## Action Auth

```tsx
export async function action({ request }: ActionFunctionArgs) {
  const token = getSessionToken(request);
  if (!token) return json({ error: "Unauthorized" }, { status: 401 });
  // process form data
  return json({ success: true });
}
```
