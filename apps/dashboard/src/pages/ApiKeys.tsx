import { useEffect, useState } from "react";
import { api, type ApiKey } from "../lib/api";

export function ApiKeys() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState("");

  useEffect(() => {
    api.apiKeys.list().then((res) => setKeys(res.data)).catch(console.error);
  }, []);

  async function handleCreate() {
    const result = await api.apiKeys.create({ name, scopes: ["gates:*"] });
    setNewKey(result.key);
    setShowCreate(false);
    setName("");
    const list = await api.apiKeys.list();
    setKeys(list.data);
  }

  async function handleRevoke(id: string) {
    await api.apiKeys.revoke(id);
    setKeys((prev) => prev.filter((k) => k.id !== id));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">API Keys ({keys.length})</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
        >
          Create Key
        </button>
      </div>

      {newKey && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm font-medium text-yellow-800 mb-1">New API Key Created</p>
          <p className="text-xs text-yellow-700 mb-2">Copy this key now — it won't be shown again.</p>
          <code className="block p-2 bg-white border border-yellow-300 rounded text-sm font-mono break-all">{newKey}</code>
          <button onClick={() => setNewKey("")} className="mt-2 text-sm text-yellow-700 hover:underline">Dismiss</button>
        </div>
      )}

      {showCreate && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h3 className="font-medium mb-3">Create API Key</h3>
          <input
            type="text"
            placeholder="Key name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Create</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Prefix</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Scopes</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Last Used</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {keys.map((k) => (
              <tr key={k.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{k.name}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{k.keyPrefix}...</td>
                <td className="px-4 py-3 text-gray-600">{k.scopes.join(", ") || "—"}</td>
                <td className="px-4 py-3 text-gray-600">{k.lastUsedAt ? new Date(k.lastUsedAt).toLocaleString() : "Never"}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleRevoke(k.id)} className="text-sm text-red-600 hover:underline">Revoke</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
