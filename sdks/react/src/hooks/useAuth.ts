import { useContext } from "react";
import { GatesContext } from "../context";
import type { GatesAuthState } from "../types";

export function useAuth(): GatesAuthState {
  const ctx = useContext(GatesContext);
  if (!ctx) {
    throw new Error("useAuth must be used within a <GatesProvider>");
  }
  return ctx;
}
