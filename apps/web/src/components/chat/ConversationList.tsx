import { useRef, useState } from "react";
import type { ConversationSession } from "../../types";
import { exportConversationUrl } from "../../api/conversations";

interface Props {
  conversations: ConversationSession[];
  activeId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
  onImport: (jsonl: string) => Promise<void>;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
}

function dateLabel(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });
}

export function ConversationList({
  conversations,
  activeId,
  loading,
  onSelect,
  onNew,
  onImport,
  onRename,
  onDelete,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [importing, setImporting] = useState(false);

  async function handleFile(file: File) {
    setImporting(true);
    try {
      await onImport(await file.text());
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <aside className="conv-list">
      <div className="conv-list-head">
        <button className="primary" onClick={onNew}>
          + 새 채팅
        </button>
        <button disabled={importing} onClick={() => fileRef.current?.click()}>
          {importing ? "가져오는 중…" : "Import"}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".jsonl,application/x-ndjson"
          style={{ display: "none" }}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
      </div>
      {loading && <p className="muted">불러오는 중…</p>}
      {!loading && conversations.length === 0 && (
        <p className="muted" style={{ padding: "0 6px", fontSize: 13 }}>
          대화가 없습니다. 새 채팅을 시작하거나 llama.app JSONL을 가져오세요.
        </p>
      )}
      {conversations.map((conv) => (
        <div
          key={conv.id}
          className={`conv-item${conv.id === activeId ? " active" : ""}`}
          onClick={() => onSelect(conv.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => event.key === "Enter" && onSelect(conv.id)}
        >
          {editingId === conv.id ? (
            <input
              autoFocus
              value={draft}
              onClick={(event) => event.stopPropagation()}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  onRename(conv.id, draft.trim() || conv.name);
                  setEditingId(null);
                }
                if (event.key === "Escape") setEditingId(null);
              }}
              onBlur={() => setEditingId(null)}
            />
          ) : (
            <span className="conv-name">{conv.name || "제목 없음"}</span>
          )}
          <span className="conv-date">{dateLabel(conv.lastModified)}</span>
          <span
            className="conv-actions"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              onClick={() => {
                setDraft(conv.name);
                setEditingId(conv.id);
              }}
            >
              이름
            </button>
            <a
              href={exportConversationUrl(conv.id)}
              download
              onClick={(event) => event.stopPropagation()}
            >
              <button tabIndex={-1}>Export</button>
            </a>
            <button
              onClick={() => {
                if (window.confirm(`"${conv.name || "제목 없음"}" 대화를 삭제할까요?`)) {
                  onDelete(conv.id);
                }
              }}
            >
              삭제
            </button>
          </span>
        </div>
      ))}
    </aside>
  );
}
