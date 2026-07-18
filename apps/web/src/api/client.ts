const STORAGE_KEY = "ts_api_url";

export function getBaseUrl(): string {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) return stored.replace(/\/$/, "");
  }
  return (import.meta.env.VITE_API_URL as string | undefined) ?? "";
}

export function setBaseUrl(url: string): void {
  const trimmed = url.trim().replace(/\/$/, "");
  if (trimmed) window.localStorage.setItem(STORAGE_KEY, trimmed);
  else window.localStorage.removeItem(STORAGE_KEY);
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${getBaseUrl()}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${response.status}: ${text || response.statusText}`);
  }
  return (await response.json()) as T;
}
