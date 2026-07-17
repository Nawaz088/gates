import { useAuth } from "../hooks/useAuth";
import type { ReactNode } from "react";

interface ProtectProps {
  children: ReactNode;
  role?: string;
  permission?: string;
}

export function Protect({ children, role, permission }: ProtectProps) {
  const { isSignedIn, orgRole } = useAuth();

  if (!isSignedIn) return null;
  if (role && orgRole !== role) return null;

  return <>{children}</>;
}
