// Thin fetch wrapper. The session lives in an HttpOnly cookie, so no token is ever
// visible to JavaScript (and so can't be stolen by an injected script).

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, typeof data.detail === "string" ? data.detail : res.statusText);
  return data as T;
}

export type Me = { username: string; display_name: string };
export type Health = { status: string; version: string; database: string };
export type Module = { name: string; state: "ready" | "planned" | "disabled"; note: string };
export type Status = { modules: Module[]; live_trading: boolean };
export type SessionRow = { id: string; created_at: string; last_seen: string; ip: string; user_agent: string; current: boolean };
export type AuditRow = { ts: string; actor: string; action: string; ip: string; detail: Record<string, unknown> };

export const api = {
  health: () => request<Health>("GET", "/health"),
  me: () => request<Me>("GET", "/auth/me"),
  login: (username: string, password: string, totp: string) =>
    request<Me>("POST", "/auth/login", { username, password, totp }),
  logout: () => request("POST", "/auth/logout"),
  status: () => request<Status>("GET", "/status"),
  sessions: () => request<SessionRow[]>("GET", "/auth/sessions"),
  revoke: (id: string) => request("DELETE", `/auth/sessions/${encodeURIComponent(id)}`),
  audit: () => request<AuditRow[]>("GET", "/audit?limit=30"),
};

export type Conversation = { id: number; title: string; created_at: string; updated_at: string };
export type ChatMessage = { id: number; role: "user" | "assistant" | "system"; content: string; created_at: string };
export type SendResult = { message: ChatMessage; reply: ChatMessage | null; notice: string | null };

export const chat = {
  list: () => request<Conversation[]>("GET", "/chat/conversations"),
  create: () => request<Conversation>("POST", "/chat/conversations", {}),
  remove: (id: number) => request("DELETE", `/chat/conversations/${id}`),
  messages: (id: number) => request<ChatMessage[]>("GET", `/chat/conversations/${id}/messages`),
  send: (id: number, content: string) => request<SendResult>("POST", `/chat/conversations/${id}/messages`, { content }),
};
