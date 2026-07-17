import { useAuth } from "../hooks/useAuth";
import type { ReactNode } from "react";

export function SignedIn({ children }: { children: ReactNode }) {
  const { isSignedIn } = useAuth();
  return isSignedIn ? <>{children}</> : null;
}
