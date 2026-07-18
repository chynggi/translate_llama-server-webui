import { useCallback, useState } from "react";
import { streamTranslate } from "../api/sse";
import type { ChatMessage, DetectedGlossary, TranslateRequest } from "../types";

export interface TranslateStreamState {
  output: string;
  detected: DetectedGlossary | null;
  messages: ChatMessage[] | null;
  tokens: Record<string, number> | null;
  busy: boolean;
  error: string;
  run: (body: TranslateRequest) => Promise<void>;
  reset: () => void;
}

export function useTranslateStream(): TranslateStreamState {
  const [output, setOutput] = useState("");
  const [detected, setDetected] = useState<DetectedGlossary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);
  const [tokens, setTokens] = useState<Record<string, number> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const reset = useCallback(() => {
    setOutput("");
    setDetected(null);
    setMessages(null);
    setTokens(null);
    setError("");
  }, []);

  const run = useCallback(async (body: TranslateRequest) => {
    setBusy(true);
    setOutput("");
    setDetected(null);
    setMessages(null);
    setTokens(null);
    setError("");
    try {
      for await (const event of streamTranslate(body)) {
        if (event.type === "delta") {
          setOutput((value) => value + String(event.content ?? ""));
        }
        if (event.type === "done") {
          setDetected(event.detected as DetectedGlossary);
          setOutput(String(event.output ?? ""));
          setMessages((event.messages as ChatMessage[]) ?? null);
          setTokens((event.tokens as Record<string, number>) ?? null);
        }
        if (event.type === "error") {
          throw new Error(String(event.message));
        }
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Translation failed");
    } finally {
      setBusy(false);
    }
  }, []);

  return { output, detected, messages, tokens, busy, error, run, reset };
}
