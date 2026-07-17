import { useState, type FormEvent } from "react";
import { useAuth } from "../hooks/useAuth";

interface SignUpProps {
  routing?: "hash" | "path" | "virtual";
  afterSignUpUrl?: string;
  signInUrl?: string;
  appearance?: Record<string, unknown>;
}

export function SignUp({ afterSignUpUrl = "/", signInUrl = "/sign-in" }: SignUpProps) {
  const { isSignedIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
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
      const resp = await fetch("/v1/sign_ups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email_address: [email],
          password,
          first_name: firstName,
          last_name: lastName,
        }),
      });
      if (!resp.ok) {
        const data = await resp.json();
        setError(data.errors?.[0]?.message || "Sign up failed.");
        return;
      }
      window.location.href = afterSignUpUrl;
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="gates-sign-up">
      <form onSubmit={handleSubmit}>
        <h2>Create Account</h2>
        {error && <div className="gates-error">{error}</div>}
        <label>
          First name
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </label>
        <label>
          Last name
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </label>
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
            minLength={8}
            autoComplete="new-password"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Creating account..." : "Create Account"}
        </button>
        <p>
          <a href={signInUrl}>Already have an account? Sign in</a>
        </p>
      </form>
    </div>
  );
}
