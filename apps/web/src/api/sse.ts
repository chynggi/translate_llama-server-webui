import { getBaseUrl } from "./client";
import type { TranslateRequest } from "../types";

export interface SseEvent {
  type: string;
  [key: string]: unknown;
}

export function parseSseBuffer(buffer: string): { events: SseEvent[]; rest: string } {
  const events: SseEvent[] = [];
  let rest = buffer;
  let idx: number;
  while ((idx = rest.search(/\r?\n\r?\n/)) !== -1) {
    const separator = rest.match(/\r?\n\r?\n/)![0];
    const rawEvent = rest.slice(0, idx);
    rest = rest.slice(idx + separator.length);
    const data = rawEvent
      .split(/\r?\n/)
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (!data) continue;
    try {
      events.push(JSON.parse(data) as SseEvent);
    } catch {
      // ignore non-JSON payloads (keep-alive comments, etc.)
    }
  }
  return { events, rest };
}

export async function* streamTranslate(
  body: TranslateRequest
): AsyncGenerator<SseEvent> {
  const response = await fetch(`${getBaseUrl()}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, stream: true }),
  });
  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`API ${response.status}: ${text}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseBuffer(buffer);
    buffer = rest;
    for (const event of events) yield event;
  }
  buffer += decoder.decode();
  const final = parseSseBuffer(buffer);
  for (const event of final.events) yield event;
}
