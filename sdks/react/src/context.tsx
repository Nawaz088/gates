import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";
import type { GatesAuthState, GatesProviderProps, GatesSession, GatesUser } from "./types";

const SESSION_COOKIE = "__session";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function decodeJwt(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    return JSON.parse(atob(parts[1]));
  } catch {
    return null;
  }
}

export const GatesContext = createContext<GatesAuthState | null>(null);

export function GatesProvider({
  children,
  afterSignInUrl = "/",
  afterSignUpUrl = "/",
}: GatesProviderProps) {
  const [state, setState] = useState<GatesAuthState>({
    isLoaded: false,
    isSignedIn: false,
    user: null,
    session: null,
    sessionId: null,
    orgId: null,
    orgRole: null,
    signOut: async () => {},
    openSignIn: () => {},
    openSignUp: () => {},
  });

  useEffect(() => {
    const token = getCookie(SESSION_COOKIE);
    if (!token) {
      setState((prev) => ({ ...prev, isLoaded: true }));
      return;
    }

    const payload = decodeJwt(token);
    if (!payload || !payload.sub || !payload.sid) {
      setState((prev) => ({ ...prev, isLoaded: true }));
      return;
    }

    const session: GatesSession = {
      id: payload.sid as string,
      userId: payload.sub as string,
      status: "active",
      lastActiveAt: "",
      expireAt: "",
    };

    const user: GatesUser = {
      id: payload.sub as string,
      firstName: null,
      lastName: null,
      imageUrl: null,
      email: (payload.email as string) || null,
      username: (payload.username as string) || null,
      twoFactorEnabled: false,
    };

    setState({
      isLoaded: true,
      isSignedIn: true,
      user,
      session,
      sessionId: payload.sid as string,
      orgId: (payload.org_id as string) || null,
      orgRole: (payload.org_role as string) || null,
      signOut: async () => {
        try {
          await fetch("/v1/sign_outs", { method: "POST" });
        } catch {
          // ignore
        }
        document.cookie = `${SESSION_COOKIE}=; path=/; max-age=0`;
        setState((prev) => ({
          ...prev,
          isSignedIn: false,
          user: null,
          session: null,
          sessionId: null,
        }));
      },
      openSignIn: () => {
        window.location.href = afterSignInUrl;
      },
      openSignUp: () => {
        window.location.href = afterSignUpUrl;
      },
    });
  }, [afterSignInUrl, afterSignUpUrl]);

  const value = useMemo(() => state, [state]);

  return <GatesContext.Provider value={value}>{children}</GatesContext.Provider>;
}
