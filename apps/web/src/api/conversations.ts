import { apiFetch, getBaseUrl } from "./client";
import type {
  AppendMessageRequest,
  AppendMessageResponse,
  ConversationDetail,
  ConversationListResponse,
  ConversationSession,
} from "../types";

export function listConversations(): Promise<ConversationListResponse> {
  return apiFetch<ConversationListResponse>("/conversations");
}

export function createConversation(body: {
  name?: string;
  thinkingEnabled?: boolean;
}): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>("/conversations", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/conversations/${id}`);
}

export function patchConversation(
  id: string,
  body: { name?: string; currNode?: string; thinkingEnabled?: boolean }
): Promise<{ session: ConversationSession }> {
  return apiFetch<{ session: ConversationSession }>(`/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteConversation(id: string): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>(`/conversations/${id}`, {
    method: "DELETE",
  });
}

export function appendMessage(
  convId: string,
  body: AppendMessageRequest
): Promise<AppendMessageResponse> {
  return apiFetch<AppendMessageResponse>(`/conversations/${convId}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function importConversation(jsonl: string): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>("/conversations/import", {
    method: "POST",
    body: JSON.stringify({ jsonl }),
  });
}

/** URL of the llama.app-compatible JSONL export (use for downloads). */
export function exportConversationUrl(id: string): string {
  return `${getBaseUrl()}/conversations/${id}/export`;
}

export function getChatSystemPrompt(): Promise<{ content: string; file: string }> {
  return apiFetch<{ content: string; file: string }>("/chat/system-prompt");
}
