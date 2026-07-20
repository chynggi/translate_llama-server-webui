import { useEffect, useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPresets } from "../api/presets";
import { ChatInput } from "../components/chat/ChatInput";
import { ConversationList } from "../components/chat/ConversationList";
import { Markdown } from "../components/chat/Markdown";
import { MessageItem } from "../components/chat/MessageItem";
import { ThinkingBlock } from "../components/chat/ThinkingBlock";
import { useChatController } from "../hooks/useChatController";
import { usePrefs } from "../theme/prefs";
import { activePath } from "../utils/conversationTree";

export function Chat() {
  const {
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
  } = useChatController();
  const { prefs } = usePrefs();
  const presetsQuery = useQuery({ queryKey: ["presets"], queryFn: getPresets });
  const scrollRef = useRef<HTMLDivElement>(null);

  const path = useMemo(
    () => activePath(conv.messages, conv.session?.currNode),
    [conv.messages, conv.session?.currNode]
  );

  // Auto-select the most recent conversation once the list arrives.
  useEffect(() => {
    if (!conv.activeId && conv.conversations.length > 0) {
      void conv.select(conv.conversations[0].id);
    }
    // conv identity changes every render; only the list matters here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conv.conversations]);

  // Keep the latest exchange in view.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [path.length, streamContent, streamReasoning]);

  async function handleImport(jsonl: string) {
    try {
      await conv.importJsonl(jsonl);
    } catch (cause) {
      window.alert(
        `가져오기 실패: ${cause instanceof Error ? cause.message : "알 수 없는 오류"}`
      );
    }
  }

  return (
    <section className="chat-shell">
      <ConversationList
        conversations={conv.conversations}
        activeId={conv.activeId}
        loading={conv.listLoading}
        onSelect={(id) => void conv.select(id)}
        onNew={() => void conv.createNew()}
        onImport={handleImport}
        onRename={(id, name) => void conv.rename(id, name)}
        onDelete={(id) => void conv.remove(id)}
      />
      <div className="chat-main">
        <div className="chat-scroll" ref={scrollRef}>
          <div className="chat-column chat-width">
            {conv.detailLoading && <p className="muted">대화를 불러오는 중…</p>}
            {!conv.session && !conv.detailLoading && (
              <div className="chat-empty">
                <h2>Translation Studio Chat</h2>
                <p>
                  왼쪽에서 대화를 선택하거나 새 채팅을 시작하세요. llama.app
                  JSONL 납출 파일을 그대로 가져올 수도 있습니다.
                </p>
                <p>
                  입력창에서 프리셋을 선택하면 글로서리 탐지 + 프롬프트 빌더가
                  적용된 번역 파이프라인으로 동작합니다.
                </p>
              </div>
            )}
            {path.map((message) => (
              <MessageItem
                key={message.id}
                messages={conv.messages}
                message={message}
                busy={busy}
                onNavigate={(leafId) => void conv.navigate(leafId)}
                onEditBranch={(m, content) => void editBranch(m, content)}
                onRegenerate={(m) => void regenerate(m)}
              />
            ))}
            {busy && (
              <div className="msg-row assistant">
                <div className="msg-bubble">
                  {(streamReasoning || prefs.showThoughtInProgress) && (
                    <ThinkingBlock reasoning={streamReasoning} inProgress />
                  )}
                  <div className="msg-content streaming">
                    {streamContent ? (
                      <Markdown content={streamContent} />
                    ) : (
                      <span className="placeholder">생성하는 중…</span>
                    )}
                  </div>
                </div>
              </div>
            )}
            {(sendError || conv.error) && (
              <p className="error">{sendError || conv.error}</p>
            )}
          </div>
        </div>
        <ChatInput
          presets={presetsQuery.data?.presets ?? []}
          preset={preset}
          onPresetChange={setPreset}
          thinkingEnabled={conv.session?.thinkingEnabled ?? false}
          onToggleThinking={(enabled) => void conv.setThinkingEnabled(enabled)}
          busy={busy}
          onSend={(text) => void send(text)}
        />
      </div>
    </section>
  );
}
