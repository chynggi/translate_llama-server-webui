import { useCallback, useState } from "react";
import { streamChatCompletion } from "../api/chat";
import type { ChatStreamRequest, ChatStreamResult } from "../api/chat";

export interface ChatStreamState {
  content: string;
  reasoning: string;
  busy: boolean;
  error: string;
  run: (body: ChatStreamRequest) => Promise<ChatStreamResult | null>;
  reset: () => void;
}

/** Progressive state for a plain (non-preset) chat completion stream. */
export function useChatStream(): ChatStreamState {
  const [content, setContent] = useState("");
  const [reasoning, setReasoning] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const reset = useCallback(() => {
    setContent("");
    setReasoning("");
    setError("");
  }, []);

  const run = useCallback(async (body: ChatStreamRequest) => {
    setBusy(true);
    setContent("");
    setReasoning("");
    setError("");
    try {
      return await streamChatCompletion(body, (nextContent, nextReasoning) => {
        setContent(nextContent);
        setReasoning(nextReasoning);
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Chat failed");
      return null;
    } finally {
      setBusy(false);
    }
  }, []);

  return { content, reasoning, busy, error, run, reset };
}
