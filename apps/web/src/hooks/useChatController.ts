import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getChatSystemPrompt } from "../api/conversations";
import { useChatStream } from "./useChatStream";
import { useConversations } from "./useConversations";
import { useTranslateStream } from "./useTranslateStream";
import type { ConversationMessage, MessageExtra } from "../types";
import { activePath, rootOf } from "../utils/conversationTree";

/** Orchestrates sending/responding inside a tree conversation: user message
 * -> translation pipeline (preset) or plain chat completion -> assistant
 * message persisted as a new branch. */
export function useChatController() {
  const conv = useConversations();
  const chatStream = useChatStream();
  const translateStream = useTranslateStream();
  const [preset, setPreset] = useState(""); // "" = plain chat
  const [sendError, setSendError] = useState("");
  const systemPromptQuery = useQuery({
    queryKey: ["chat-system-prompt"],
    queryFn: getChatSystemPrompt,
    staleTime: Infinity,
  });

  const busy = chatStream.busy || translateStream.busy;
  const streamContent = preset ? translateStream.output : chatStream.content;
  const streamReasoning = preset ? translateStream.reasoning : chatStream.reasoning;

  function buildContext(
    messages: ConversationMessage[],
    leafId: string
  ): { role: string; content: string }[] {
    const fallbackSystem = systemPromptQuery.data?.content ?? "";
    return activePath(messages, leafId)
      .map((message) => {
        if (message.role === "system") {
          const content = message.content.trim() || fallbackSystem;
          return content ? { role: "system", content } : null;
        }
        if (message.role === "user" || message.role === "assistant") {
          return message.content
            ? { role: message.role, content: message.content }
            : null;
        }
        return null;
      })
      .filter((m): m is { role: string; content: string } => m !== null);
  }

  /** Run the assistant response and persist it as a child of `userMsg` —
   * every response is a new branch in the message tree. */
  async function respondWith(
    userMsg: ConversationMessage,
    contextMessages: ConversationMessage[]
  ) {
    if (preset) {
      const result = await translateStream.run({ source: userMsg.content, preset });
      if (!result) {
        setSendError(translateStream.error || "번역 실패");
        return;
      }
      const extra: MessageExtra[] = [
        {
          type: "TRANSLATION_META",
          preset,
          log_id: result.logId || undefined,
          detected: result.detected ?? undefined,
          messages: result.messages ?? undefined,
          tokens: result.tokens ?? undefined,
        },
      ];
      await conv.post({
        parent: userMsg.id,
        role: "assistant",
        content: result.output,
        model: result.model || undefined,
        reasoningContent: result.reasoning || undefined,
        timings: result.timings ?? undefined,
        extra,
      });
      return;
    }

    const messages = buildContext(contextMessages, userMsg.id);
    const result = await chatStream.run({
      messages,
      ...(conv.session?.thinkingEnabled
        ? { chat_template_kwargs: { enable_thinking: true } }
        : {}),
    });
    if (!result) {
      setSendError(chatStream.error || "생성 실패");
      return;
    }
    await conv.post({
      parent: userMsg.id,
      role: "assistant",
      content: result.content,
      reasoningContent: result.reasoning || undefined,
      timings: result.timings ?? undefined,
      model: result.model || undefined,
      completionId: result.completionId || undefined,
    });
  }

  async function send(text: string) {
    setSendError("");
    try {
      let session = conv.session;
      let messages = conv.messages;
      if (!session) {
        const detail = await conv.createNew();
        session = detail.session;
        messages = detail.messages;
      }
      const leafId = session.currNode ?? rootOf(messages)?.id;
      if (!leafId) throw new Error("대화에 루트 메시지가 없습니다.");

      const userMsg = await conv.post({ parent: leafId, role: "user", content: text });
      if (!session.name) {
        const title = text.split(/\s+/).slice(0, 6).join(" ").slice(0, 48);
        void conv.rename(session.id, title);
      }
      await respondWith(userMsg, [...messages, userMsg]);
    } catch (cause) {
      setSendError(cause instanceof Error ? cause.message : "전송 실패");
    }
  }

  async function regenerate(assistantMsg: ConversationMessage) {
    if (!assistantMsg.parent) return;
    const parentMsg = conv.messages.find((m) => m.id === assistantMsg.parent);
    if (!parentMsg) return;
    setSendError("");
    await respondWith(parentMsg, conv.messages);
  }

  async function editBranch(message: ConversationMessage, content: string) {
    if (!message.parent) return;
    setSendError("");
    try {
      const userMsg = await conv.post({
        parent: message.parent,
        role: "user",
        content,
      });
      await respondWith(userMsg, [...conv.messages, userMsg]);
    } catch (cause) {
      setSendError(cause instanceof Error ? cause.message : "편집 실패");
    }
  }

  return {
    conv,
    preset,
    setPreset,
    busy,
    streamContent,
    streamReasoning,
    sendError,
    send,
    regenerate,
    editBranch,
  };
}
