import { useEffect, useState } from "react";
import { api, type WebhookEndpoint } from "../lib/api";

export function Webhooks() {
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [events, setEvents] = useState<string[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [url, setUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [newSecret, setNewSecret] = useState("");

  useEffect(() => {
    api.webhooks.listEndpoints().then((res) => setEndpoints(res.data)).catch(console.error);
    api.webhooks.listEvents().then((res) => setEvents(res.data)).catch(console.error);
  }, []);

  function toggleEvent(event: string) {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event],
    );
  }

  async function handleCreate() {
    const result = await api.webhooks.createEndpoint({ url, events: selectedEvents });
    setNewSecret(result.secret);
    setShowCreate(false);
    setUrl("");
    setSelectedEvents([]);
    const list = await api.webhooks.listEndpoints();
    setEndpoints(list.data);
  }

  async function handleDelete(id: string) {
    await api.webhooks.deleteEndpoint(id);
    setEndpoints((prev) => prev.filter((e) => e.id !== id));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Webhooks ({endpoints.length})</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
        >
          Add Endpoint
        </button>
      </div>

      {newSecret && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm font-medium text-yellow-800 mb-1">Webhook Secret</p>
          <code className="block p-2 bg-white border border-yellow-300 rounded text-sm font-mono break-all">{newSecret}</code>
          <button onClick={() => setNewSecret("")} className="mt-2 text-sm text-yellow-700 hover:underline">Dismiss</button>
        </div>
      )}

      {showCreate && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h3 className="font-medium mb-3">New Webhook Endpoint</h3>
          <input
            type="url"
            placeholder="https://example.com/webhook"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
          />
          <div className="mb-3">
            <p className="text-sm font-medium text-gray-700 mb-2">Events</p>
            <div className="grid grid-cols-3 gap-2">
              {events.slice(0, 12).map((event) => (
                <label key={event} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedEvents.includes(event)}
                    onChange={() => toggleEvent(event)}
                    className="rounded"
                  />
                  {event}
                </label>
              ))}
            </div>
          </div>
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
              <th className="text-left px-4 py-3 font-medium text-gray-500">URL</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Events</th>
              <th className="text-center px-4 py-3 font-medium text-gray-500">Enabled</th>
              <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {endpoints.map((ep) => (
              <tr key={ep.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-600 max-w-xs truncate">{ep.url}</td>
                <td className="px-4 py-3 text-gray-600">{ep.events.slice(0, 3).join(", ")}{ep.events.length > 3 ? "..." : ""}</td>
                <td className="px-4 py-3 text-center">
                  {ep.enabled ? (
                    <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Enabled</span>
                  ) : (
                    <span className="inline-block px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full">Disabled</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => handleDelete(ep.id)} className="text-sm text-red-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
