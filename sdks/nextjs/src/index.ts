import { cookies } from "next/headers.js";

const SESSION_COOKIE = "__session";

interface AuthResult {
  userId: string | null;
  sessionId: string | null;
  orgId: string | null;
  orgRole: string | null;
  isSignedIn: boolean;
}

function decodeJwt(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    return JSON.parse(Buffer.from(parts[1], "base64").toString());
  } catch {
    return null;
  }
}

export async function auth(): Promise<AuthResult> {
  const cookieStore = cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (!token) {
    return { userId: null, sessionId: null, orgId: null, orgRole: null, isSignedIn: false };
  }

  const payload = decodeJwt(token);
  if (!payload || !payload.sub || !payload.sid) {
    return { userId: null, sessionId: null, orgId: null, orgRole: null, isSignedIn: false };
  }

  return {
    userId: payload.sub as string,
    sessionId: payload.sid as string,
    orgId: (payload.org_id as string) || null,
    orgRole: (payload.org_role as string) || null,
    isSignedIn: true,
  };
}

interface CurrentUserResult {
  id: string;
  email?: string;
  username?: string;
}

export async function currentUser(): Promise<CurrentUserResult | null> {
  const cookieStore = cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (!token) return null;

  const payload = decodeJwt(token);
  if (!payload || !payload.sub) return null;

  return {
    id: payload.sub as string,
    email: payload.email as string | undefined,
    username: payload.username as string | undefined,
  };
}

export function createRouteMatcher(routes: string[]) {
  return (pathname: string): boolean => {
    return routes.some((route) => {
      if (route.endsWith("*")) {
        return pathname.startsWith(route.slice(0, -1));
      }
      return pathname === route;
    });
  };
}

export function gatesMiddleware(authResult: AuthResult) {
  return {
    protect: () => {
      if (!authResult.isSignedIn) {
        return Response.redirect(new URL("/sign-in", process.env.GATES_PUBLIC_URL));
      }
      return null;
    },
  };
}
