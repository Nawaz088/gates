export interface GatesUser {
  id: string;
  firstName: string | null;
  lastName: string | null;
  imageUrl: string | null;
  email: string | null;
  username: string | null;
  twoFactorEnabled: boolean;
}

export interface GatesSession {
  id: string;
  userId: string;
  status: string;
  lastActiveAt: string;
  expireAt: string;
}

export interface GatesAuthState {
  isLoaded: boolean;
  isSignedIn: boolean;
  user: GatesUser | null;
  session: GatesSession | null;
  sessionId: string | null;
  orgId: string | null;
  orgRole: string | null;
  signOut: () => Promise<void>;
  openSignIn: () => void;
  openSignUp: () => void;
}

export interface GatesProviderProps {
  publishableKey: string;
  children: React.ReactNode;
  appearance?: Record<string, unknown>;
  afterSignInUrl?: string;
  afterSignUpUrl?: string;
  signInUrl?: string;
  signUpUrl?: string;
}
