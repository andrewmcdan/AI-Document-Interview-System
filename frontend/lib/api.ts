export type ApiConfig = {
  baseUrl: string;
  token?: string;
  devUserId?: string;
};

function headers(config: ApiConfig): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (config.token) h["Authorization"] = `Bearer ${config.token}`;
  if (!config.token && config.devUserId) h["X-User-Id"] = config.devUserId;
  return h;
}

export async function postJson<T>(config: ApiConfig, path: string, body: any): Promise<T> {
  const res = await fetch(`${config.baseUrl}${path}`, {
    method: "POST",
    headers: headers(config),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJson<T>(config: ApiConfig, path: string): Promise<T> {
  const res = await fetch(`${config.baseUrl}${path}`, { headers: headers(config) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchDocuments(config: ApiConfig) {
  return getJson<Array<{ id: string; title: string; description?: string; created_at?: string }>>(config, "/documents");
}
