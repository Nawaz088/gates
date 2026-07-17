import { useContext } from "react";
import { GatesContext } from "../context";
import type { GatesSession } from "../types";

export function useSession(): { isLoaded: boolean; isSignedIn: boolean; session: GatesSession | null } {
  const ctx = useContext(GatesContext);
  if (!ctx) {
    throw new Error("useSession must be used within a <GatesProvider>");
  }
  return {
    isLoaded: ctx.isLoaded,
    isSignedIn: ctx.isSignedIn,
    session: ctx.session,
  };
}
