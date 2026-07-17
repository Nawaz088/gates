import { useEffect, useState } from "react";
import { api } from "../lib/api";

export function Dashboard() {
  const [stats, setStats] = useState({ users: 0, sessions: 0, apiKeys: 0, webhooks: 0 });

  useEffect(() => {
    Promise.all([
      api.users.list(0, 1),
      api.sessions.list(),
      api.apiKeys.list(),
      api.webhooks.listEndpoints(),
    ]).then(([users, sessions, keys, webhooks]) => {
      setStats({
        users: users.total_count,
        sessions: sessions.total_count,
        apiKeys: keys.total_count,
        webhooks: webhooks.total_count,
      });
    }).catch(console.error);
  }, []);

  const cards = [
    { label: "Users", value: stats.users, color: "bg-blue-500" },
    { label: "Active Sessions", value: stats.sessions, color: "bg-green-500" },
    { label: "API Keys", value: stats.apiKeys, color: "bg-purple-500" },
    { label: "Webhooks", value: stats.webhooks, color: "bg-orange-500" },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => (
          <div key={card.label} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className={`w-12 h-12 ${card.color} rounded-lg flex items-center justify-center mb-4`}>
              <span className="text-white text-xl font-bold">{card.value}</span>
            </div>
            <h3 className="text-sm font-medium text-gray-500">{card.label}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}
