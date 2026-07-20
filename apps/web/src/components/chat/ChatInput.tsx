import { useRef, useState } from "react";
import type { Preset } from "../../types";
import { usePrefs } from "../../theme/prefs";

interface Props {
  presets: Preset[];
  preset: string; // "" = plain chat
  onPresetChange: (id: string) => void;
  thinkingEnabled: boolean;
  onToggleThinking: (enabled: boolean) => void;
  busy: boolean;
  onSend: (text: string) => void;
}

export function ChatInput({
  presets,
  preset,
  onPresetChange,
  thinkingEnabled,
  onToggleThinking,
  busy,
  onSend,
}: Props) {
  const { prefs } = usePrefs();
  const [text, setText] = useState("");
  const areaRef = useRef<HTMLTextAreaElement>(null);

  function autoGrow() {
    const area = areaRef.current;
    if (!area) return;
    area.style.height = "auto";
    area.style.height = `${Math.min(area.scrollHeight, 220)}px`;
  }

  function submit() {
    const value = text.trim();
    if (!value || busy) return;
    setText("");
    requestAnimationFrame(autoGrow);
    onSend(value);
  }

  return (
    <div className="chat-input-area">
      <div className="chat-width" style={{ margin: "0 auto" }}>
        <div className={`chat-input-box glass-focus-ring${busy ? " streaming" : ""}`}>
          <textarea
            ref={areaRef}
            rows={1}
            value={text}
            placeholder={
              preset
                ? "번역할 일본어 원문을 입력하세요…"
                : "메시지를 입력하세요…"
            }
            onChange={(event) => {
              setText(event.target.value);
              autoGrow();
            }}
            onKeyDown={(event) => {
              if (event.key !== "Enter") return;
              const send = prefs.sendOnEnter ? !event.shiftKey : event.shiftKey;
              if (send && !event.nativeEvent.isComposing) {
                event.preventDefault();
                submit();
              }
            }}
          />
          <div className="chat-toolbar">
            <div className="left">
              <select
                value={preset}
                onChange={(event) => onPresetChange(event.target.value)}
                title="프리셋을 선택하면 번역 파이프라인(글로서리 탐지 + 프롬프트 빌더)으로 동작합니다"
              >
                <option value="">일반 채팅</option>
                {presets.map((item) => (
                  <option key={item.id} value={item.id}>
                    번역: {item.name}
                  </option>
                ))}
              </select>
              <label
                className="checkbox-row"
                style={{ fontSize: 12, color: "var(--muted-foreground)" }}
                title="reasoning 모델의 사고(thinking) 사용"
              >
                <input
                  type="checkbox"
                  checked={thinkingEnabled}
                  onChange={(event) => onToggleThinking(event.target.checked)}
                />
                thinking
              </label>
            </div>
            <button
              className="primary chat-send"
              disabled={busy || !text.trim()}
              onClick={submit}
            >
              {busy ? "생성 중…" : preset ? "번역" : "전송"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
