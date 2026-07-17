import { useEffect, useState } from "react";
import { api, type User } from "../lib/api";

export function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.users.list().then((res) => {
      setUsers(res.data);
      setTotal(res.total_count);
    }).catch(console.error);
  }, []);

  async function handleBan(id: string) {
    await api.users.ban(id);
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, banned: true } : u)));
  }

  async function handleUnban(id: string) {
    await api.users.unban(id);
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, banned: false } : u)));
  }

  const filtered = users.filter(
    (u) =>
      !search ||
      u.id.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase()) ||
      u.firstName?.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Users ({total})</h2>
        <input
          type="text"
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-500">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Email</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Username</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500">Status</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filtered.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{user.id}</td>
                <td className="px-4 py-3 font-medium">{user.firstName || ""} {user.lastName || ""}</td>
                <td className="px-4 py-3 text-gray-600">{user.email || "—"}</td>
                <td className="px-4 py-3 text-gray-600">{user.username || "—"}</td>
                <td className="px-4 py-3 text-center">
                  {user.banned ? (
                    <span className="inline-block px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">Banned</span>
                  ) : (
                    <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Active</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right space-x-2">
                  {user.banned ? (
                    <button onClick={() => handleUnban(user.id)} className="text-sm text-green-600 hover:underline">Unban</button>
                  ) : (
                    <button onClick={() => handleBan(user.id)} className="text-sm text-red-600 hover:underline">Ban</button>
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
