import { useState } from "react";
import type { ConversationMessage, PreviewResult } from "../../types";
import { translationMetaOf } from "../../types";
import { usePrefs } from "../../theme/prefs";
import { PromptPreviewPanel } from "../prompt/PromptPreviewPanel";
import { AppliedGlossary } from "./AppliedGlossary";
import { Markdown } from "./Markdown";
import { MessageStats } from "./MessageStats";
import { SiblingNav } from "./SiblingNav";
import { ThinkingBlock } from "./ThinkingBlock";

interface Props {
  messages: ConversationMessage[];
  message: ConversationMessage;
  busy: boolean;
  onNavigate: (leafId: string) => void;
  onEditBranch: (message: ConversationMessage, content: string) => void;
  onRegenerate: (message: ConversationMessage) => void;
}

function copyText(content: string) {
  void navigator.clipboard?.writeText(content).catch(() => undefined);
}

function timeLabel(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function MessageItem({
  messages,
  message,
  busy,
  onNavigate,
  onEditBranch,
  onRegenerate,
}: Props) {
  const { prefs } = usePrefs();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(message.content);
  const [showGlossary, setShowGlossary] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);

  if (message.role === "system") {
    if (!message.content.trim()) return null;
    return (
      <div className="msg-row system">
        <div className="msg-bubble">
          <div className="msg-content">
            <div className="translation-tag">System</div>
            <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>
          </div>
        </div>
      </div>
    );
  }

  const isUser = message.role === "user";
  const meta = !isUser ? translationMetaOf(message) : undefined;

  return (
    <div className={`msg-row ${isUser ? "user" : "assistant"}`}>
      <div className="msg-bubble">
        {!isUser && message.reasoningContent && (
          <ThinkingBlock reasoning={message.reasoningContent} />
        )}
        <div className="msg-content">
          {editing ? (
            <div className="msg-edit">
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
              />
              <div className="msg-edit-actions">
                <button onClick={() => setEditing(false)}>취소</button>
                <button
                  className="primary"
                  disabled={!draft.trim() || busy}
                  onClick={() => {
                    setEditing(false);
                    onEditBranch(message, draft.trim());
                  }}
                >
                  저장 후 재전송
                </button>
              </div>
            </div>
          ) : isUser && !prefs.renderUserContentAsMarkdown ? (
            <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>
          ) : (
            <Markdown content={message.content} />
          )}
        </div>
        {meta && (
          <div className="msg-actions always">
            <span className="translation-tag">번역 · {meta.preset}</span>
            <button onClick={() => setShowGlossary((v) => !v)}>
              적용 글로서리{meta.detected ? ` (${meta.detected.total})` : ""}
            </button>
            <button onClick={() => setShowPrompt((v) => !v)}>Prompt 보기</button>
          </div>
        )}
        {showGlossary && meta && (
          <AppliedGlossary detected={meta.detected ?? null} />
        )}
        {showPrompt && meta?.messages && (
          <PromptPreviewPanel result={promptPreviewOf(message)} />
        )}
        <div className="msg-meta">
          <span>{isUser ? "You" : (message.model ?? "assistant")}</span>
          <span>{timeLabel(message.timestamp)}</span>
          <SiblingNav
            messages={messages}
            message={message}
            onNavigate={onNavigate}
          />
          <span className="msg-actions">
            <button onClick={() => copyText(message.content)}>복사</button>
            {isUser && (
              <button
                disabled={busy}
                onClick={() => {
                  setDraft(message.content);
                  setEditing(true);
                }}
              >
                편집
              </button>
            )}
            {!isUser && (
              <button disabled={busy} onClick={() => onRegenerate(message)}>
                재생성
              </button>
            )}
          </span>
        </div>
        {!isUser && prefs.showMessageStats && message.timings && (
          <MessageStats timings={message.timings} />
        )}
      </div>
    </div>
  );
}

function promptPreviewOf(message: ConversationMessage): PreviewResult {
  const meta = translationMetaOf(message);
  return {
    messages: meta?.messages ?? [],
    parts: {
      system_rules: "",
      preset: "",
      glossary: "",
      user_instruction: "",
      source: "",
    },
    detected: meta?.detected ?? { categories: {}, total: 0 },
    token_count: meta?.tokens?.prompt_tokens ?? 0,
    model: message.model ?? "",
    preset: meta?.preset ?? "",
  };
}
