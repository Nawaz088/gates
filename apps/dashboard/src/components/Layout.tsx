import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

const navItems = [
  { path: "/", label: "Dashboard", icon: "📊" },
  { path: "/users", label: "Users", icon: "👤" },
  { path: "/sessions", label: "Sessions", icon: "🔑" },
  { path: "/api-keys", label: "API Keys", icon: "🔐" },
  { path: "/webhooks", label: "Webhooks", icon: "🔔" },
  { path: "/audit-log", label: "Audit Log", icon: "📋" },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Gates Dashboard</h1>
          <p className="text-sm text-gray-500">Tenant Admin</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto bg-gray-50 p-6">{children}</main>
    </div>
  );
}
