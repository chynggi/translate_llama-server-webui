import { getBaseUrl } from "./client";
import { parseSseBuffer } from "./sse";
import type { MessageTimings } from "../types";

export interface ChatCompletionMessage {
  role: string;
  content: string;
}

export interface ChatStreamRequest {
  model?: string;
  messages: ChatCompletionMessage[];
  chat_template_kwargs?: Record<string, unknown>;
  [key: string]: unknown; // sampling params; middleware fills server defaults
}

export interface ChatStreamResult {
  content: string;
  reasoning: string;
  timings: MessageTimings | null;
  model: string;
  completionId: string;
}

interface OpenAiChunk {
  id?: string;
  model?: string;
  choices?: { delta?: { content?: string; reasoning_content?: string } }[];
  timings?: MessageTimings;
  error?: { message?: string } | string;
}

/**
 * Stream an OpenAI-compatible chat completion through the middleware proxy.
 * Handles llama-server specifics: `delta.reasoning_content` (thinking) and the
 * `timings` object attached to the final chunk.
 */
export async function streamChatCompletion(
  body: ChatStreamRequest,
  onDelta: (content: string, reasoning: string) => void
): Promise<ChatStreamResult> {
  const response = await fetch(`${getBaseUrl()}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, stream: true }),
  });
  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`API ${response.status}: ${text}`);
  }

  let content = "";
  let reasoning = "";
  let model = "";
  let completionId = "";
  let timings: MessageTimings | null = null;

  const handle = (chunk: OpenAiChunk) => {
    if (chunk.error) {
      const message =
        typeof chunk.error === "string"
          ? chunk.error
          : chunk.error.message ?? "upstream error";
      throw new Error(message);
    }
    if (chunk.id) completionId = chunk.id;
    if (chunk.model) model = chunk.model;
    if (chunk.timings) timings = chunk.timings;
    const delta = chunk.choices?.[0]?.delta;
    if (delta?.reasoning_content) reasoning += delta.reasoning_content;
    if (delta?.content) content += delta.content;
    onDelta(content, reasoning);
  };

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSseBuffer(buffer);
    buffer = rest;
    for (const event of events) handle(event as unknown as OpenAiChunk);
  }
  buffer += decoder.decode();
  const final = parseSseBuffer(buffer);
  for (const event of final.events) handle(event as unknown as OpenAiChunk);

  return { content, reasoning, timings, model, completionId };
}
