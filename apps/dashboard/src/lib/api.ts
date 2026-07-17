const BASE = "/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers as Record<string, string> },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.errors?.[0]?.message || `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export interface User {
  id: string;
  firstName: string | null;
  lastName: string | null;
  email: string | null;
  username: string | null;
  banned: boolean;
  twoFactorEnabled: boolean;
  lastSignInAt: string | null;
  createdAt: string;
}

export interface ApiKey {
  id: string;
  name: string;
  keyPrefix: string;
  scopes: string[];
  lastUsedAt: string | null;
  createdAt: string;
}

export interface WebhookEndpoint {
  id: string;
  url: string;
  events: string[];
  enabled: boolean;
}

export const api = {
  users: {
    list: (offset = 0, limit = 100) =>
      request<{ data: User[]; total_count: number }>(`/users?offset=${offset}&limit=${limit}`),
    ban: (id: string) => request<User>(`/users/${id}/ban`, { method: "POST" }),
    unban: (id: string) => request<User>(`/users/${id}/unban`, { method: "POST" }),
    lock: (id: string) => request<User>(`/users/${id}/lock`, { method: "POST" }),
    unlock: (id: string) => request<User>(`/users/${id}/unlock`, { method: "POST" }),
  },
  sessions: {
    list: () => request<{ data: { id: string; userId: string; status: string; lastActiveAt: string }[]; total_count: number }>("/sessions"),
    revoke: (id: string) => request(`/sessions/${id}/revoke`, { method: "POST" }),
  },
  apiKeys: {
    list: () => request<{ data: ApiKey[]; total_count: number }>("/api_keys"),
    create: (data: { name: string; scopes: string[] }) =>
      request<{ id: string; key: string }>("/api_keys", { method: "POST", body: JSON.stringify(data) }),
    revoke: (id: string) => request(`/api_keys/${id}`, { method: "DELETE" }),
  },
  webhooks: {
    listEndpoints: () =>
      request<{ data: WebhookEndpoint[]; total_count: number }>("/webhooks/endpoints"),
    createEndpoint: (data: { url: string; events: string[] }) =>
      request<{ id: string; secret: string }>("/webhooks/endpoints", {
        method: "POST",
        body: JSON.stringify({ ...data, enabled: true }),
      }),
    deleteEndpoint: (id: string) => request(`/webhooks/endpoints/${id}`, { method: "DELETE" }),
    listEvents: () => request<{ data: string[] }>("/webhooks/endpoints/events"),
  },
};
