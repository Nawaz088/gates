import { useState } from "react";
import { useUser } from "../hooks/useUser";
import { useAuth } from "../hooks/useAuth";

export function UserProfile() {
  const { user } = useUser();
  const { signOut } = useAuth();
  const [tab, setTab] = useState<"account" | "security">("account");

  if (!user) return null;

  return (
    <div className="gates-user-profile">
      <h2>Profile</h2>

      <div className="gates-tabs">
        <button
          onClick={() => setTab("account")}
          className={tab === "account" ? "active" : ""}
        >
          Account
        </button>
        <button
          onClick={() => setTab("security")}
          className={tab === "security" ? "active" : ""}
        >
          Security
        </button>
      </div>

      {tab === "account" && (
        <div className="gates-tab-content">
          <div className="gates-field">
            <label>Name</label>
            <p>
              {user.firstName} {user.lastName}
            </p>
          </div>
          <div className="gates-field">
            <label>Email</label>
            <p>{user.email}</p>
          </div>
          <div className="gates-field">
            <label>Username</label>
            <p>{user.username || "—"}</p>
          </div>
        </div>
      )}

      {tab === "security" && (
        <div className="gates-tab-content">
          <p>Two-factor authentication: {user.twoFactorEnabled ? "Enabled" : "Not enabled"}</p>
          <button onClick={signOut} className="gates-danger-button">
            Sign out of all devices
          </button>
        </div>
      )}
    </div>
  );
}
