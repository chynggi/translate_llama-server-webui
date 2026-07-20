import { useCallback, useState } from "react";
import { streamTranslate } from "../api/sse";
import type {
  ChatMessage,
  DetectedGlossary,
  MessageTimings,
  TranslateRequest,
} from "../types";

export interface TranslateStreamResult {
  output: string;
  reasoning: string;
  detected: DetectedGlossary | null;
  messages: ChatMessage[] | null;
  tokens: Record<string, number> | null;
  timings: MessageTimings | null;
  model: string;
  logId: string;
}

export interface TranslateStreamState {
  output: string;
  reasoning: string;
  detected: DetectedGlossary | null;
  messages: ChatMessage[] | null;
  tokens: Record<string, number> | null;
  busy: boolean;
  error: string;
  run: (body: TranslateRequest) => Promise<TranslateStreamResult | null>;
  reset: () => void;
}

export function useTranslateStream(): TranslateStreamState {
  const [output, setOutput] = useState("");
  const [reasoning, setReasoning] = useState("");
  const [detected, setDetected] = useState<DetectedGlossary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);
  const [tokens, setTokens] = useState<Record<string, number> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const reset = useCallback(() => {
    setOutput("");
    setReasoning("");
    setDetected(null);
    setMessages(null);
    setTokens(null);
    setError("");
  }, []);

  const run = useCallback(
    async (body: TranslateRequest): Promise<TranslateStreamResult | null> => {
      setBusy(true);
      setOutput("");
      setReasoning("");
      setDetected(null);
      setMessages(null);
      setTokens(null);
      setError("");
      let final: TranslateStreamResult | null = null;
      let content = "";
      let reasoningText = "";
      try {
        for await (const event of streamTranslate(body)) {
          if (event.type === "delta") {
            content += String(event.content ?? "");
            setOutput(content);
          }
          if (event.type === "reasoning") {
            reasoningText += String(event.content ?? "");
            setReasoning(reasoningText);
          }
          if (event.type === "done") {
            const doneReasoning = String(event.reasoning_content ?? reasoningText);
            final = {
              output: String(event.output ?? content),
              reasoning: doneReasoning,
              detected: (event.detected as DetectedGlossary) ?? null,
              messages: (event.messages as ChatMessage[]) ?? null,
              tokens: (event.tokens as Record<string, number>) ?? null,
              timings: (event.timings as MessageTimings) ?? null,
              model: String(event.model ?? ""),
              logId: String(event.id ?? ""),
            };
            setDetected(final.detected);
            setOutput(final.output);
            setReasoning(doneReasoning);
            setMessages(final.messages);
            setTokens(final.tokens);
          }
          if (event.type === "error") {
            throw new Error(String(event.message));
          }
        }
        return final;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Translation failed");
        return null;
      } finally {
        setBusy(false);
      }
    },
    []
  );

  return {
    output,
    reasoning,
    detected,
    messages,
    tokens,
    busy,
    error,
    run,
    reset,
  };
}
