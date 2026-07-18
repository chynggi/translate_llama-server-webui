import { apiFetch, getBaseUrl } from "./client";
import type { GlossaryEntry, GlossaryResponse } from "../types";

export function getGlossary(q?: string, category?: string): Promise<GlossaryResponse> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (category) params.set("category", category);
  const query = params.toString();
  return apiFetch<GlossaryResponse>(`/glossary${query ? `?${query}` : ""}`);
}

export interface UpsertInput {
  category: string;
  source: string;
  ko: string;
  aliases: string[];
}

export function upsertEntry(input: UpsertInput): Promise<GlossaryEntry> {
  return apiFetch<GlossaryEntry>("/glossary", {
    method: "POST",
    body: JSON.stringify({ action: "upsert", ...input }),
  });
}

export function importYaml(yaml: string): Promise<{ imported: Record<string, number> }> {
  return apiFetch<{ imported: Record<string, number> }>("/glossary", {
    method: "POST",
    body: JSON.stringify({ action: "import", yaml }),
  });
}

export async function exportYaml(category?: string): Promise<string> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  const query = params.toString();
  const response = await fetch(`${getBaseUrl()}/glossary/export${query ? `?${query}` : ""}`);
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${response.status}: ${text || response.statusText}`);
  }
  return response.text();
}
