import { useEffect, useState } from "react";
import { api } from "../lib/api";

interface Session {
  id: string;
  userId: string;
  status: string;
  lastActiveAt: string;
}

export function Sessions() {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    api.sessions.list().then((res) => setSessions(res.data)).catch(console.error);
  }, []);

  async function handleRevoke(id: string) {
    await api.sessions.revoke(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Sessions ({sessions.length})</h2>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-500">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">User ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Last Active</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sessions.map((s) => (
              <tr key={s.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.id}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.userId}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                    s.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                  }`}>{s.status}</span>
                </td>
                <td className="px-4 py-3 text-gray-600">{new Date(s.lastActiveAt).toLocaleString()}</td>
                <td className="px-4 py-3 text-right">
                  {s.status === "active" && (
                    <button onClick={() => handleRevoke(s.id)} className="text-sm text-red-600 hover:underline">Revoke</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
