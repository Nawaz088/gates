import { useState, type FormEvent } from "react";
import { useAuth } from "../hooks/useAuth";

interface SignInProps {
  routing?: "hash" | "path" | "virtual";
  afterSignInUrl?: string;
  signUpUrl?: string;
  appearance?: Record<string, unknown>;
}

export function SignIn({ afterSignInUrl = "/", signUpUrl = "/sign-up" }: SignInProps) {
  const { isSignedIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isSignedIn) {
    return <div className="gates-signed-in">You are already signed in.</div>;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const resp = await fetch("/v1/sign_ins", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: email, password }),
      });
      if (!resp.ok) {
        const data = await resp.json();
        setError(data.errors?.[0]?.message || "Sign in failed.");
        return;
      }
      window.location.href = afterSignInUrl;
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="gates-sign-in">
      <form onSubmit={handleSubmit}>
        <h2>Sign In</h2>
        {error && <div className="gates-error">{error}</div>}
        <label>
          Email address
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign In"}
        </button>
        <p>
          <a href={signUpUrl}>Don't have an account? Sign up</a>
        </p>
      </form>
    </div>
  );
}
