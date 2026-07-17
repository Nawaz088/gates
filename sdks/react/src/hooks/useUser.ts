import { useContext } from "react";
import { GatesContext } from "../context";
import type { GatesUser } from "../types";

export function useUser(): { isLoaded: boolean; isSignedIn: boolean; user: GatesUser | null } {
  const ctx = useContext(GatesContext);
  if (!ctx) {
    throw new Error("useUser must be used within a <GatesProvider>");
  }
  return {
    isLoaded: ctx.isLoaded,
    isSignedIn: ctx.isSignedIn,
    user: ctx.user,
  };
}
