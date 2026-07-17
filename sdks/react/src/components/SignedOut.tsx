import { useAuth } from "../hooks/useAuth";
import type { ReactNode } from "react";

export function SignedOut({ children }: { children: ReactNode }) {
  const { isSignedIn } = useAuth();
  return !isSignedIn ? <>{children}</> : null;
}
