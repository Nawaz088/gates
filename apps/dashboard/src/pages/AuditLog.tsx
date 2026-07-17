import { useEffect, useState } from "react";

interface AuditEntry {
  id: string;
  event: string;
  actor_id: string;
  ip_address: string | null;
  created_at: string;
}

export function AuditLog() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);

  useEffect(() => {
    fetch("/v1/audit_logs")
      .then((r) => r.json())
      .then((data) => setLogs(data.data || []))
      .catch(console.error);
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Audit Log</h2>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Event</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Actor</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">IP</th>
              <th className="text-left px-4 py-3 font-medium text-gray-500">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{log.event}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{log.actor_id}</td>
                <td className="px-4 py-3 text-gray-600">{log.ip_address || "—"}</td>
                <td className="px-4 py-3 text-gray-600">{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && (
          <p className="p-4 text-center text-gray-500">No audit log entries found.</p>
        )}
      </div>
    </div>
  );
}
