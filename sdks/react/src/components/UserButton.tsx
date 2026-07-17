import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

export function UserButton() {
  const { user, signOut } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) return null;

  const initials = [user.firstName, user.lastName]
    .filter(Boolean)
    .map((n) => n?.charAt(0).toUpperCase())
    .join("");

  return (
    <div className="gates-user-button">
      <button
        onClick={() => setOpen(!open)}
        className="gates-avatar"
        aria-label="User menu"
      >
        {user.imageUrl ? (
          <img src={user.imageUrl} alt="" className="gates-avatar-img" />
        ) : (
          <span className="gates-avatar-fallback">{initials || "?"}</span>
        )}
      </button>

      {open && (
        <div className="gates-dropdown">
          <div className="gates-dropdown-header">
            <strong>
              {user.firstName} {user.lastName}
            </strong>
            <span className="gates-email">{user.email}</span>
          </div>
          <hr />
          <button
            onClick={() => {
              signOut();
              setOpen(false);
            }}
            className="gates-dropdown-item"
          >
            Sign out
          </button>
        </div>
      )}

      {open && <div className="gates-overlay" onClick={() => setOpen(false)} />}
    </div>
  );
}
