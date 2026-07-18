import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { preview } from "../api/preview";
import { getPresets } from "../api/presets";
import { AppliedGlossary } from "../components/chat/AppliedGlossary";
import { PageHeader } from "../components/layout/Sidebar";
import { PromptPreviewPanel } from "../components/prompt/PromptPreviewPanel";
import { useTranslateStream } from "../hooks/useTranslateStream";
import type { PreviewResult } from "../types";

export function Chat() {
  const [source, setSource] = useState("");
  const [preset, setPreset] = useState("bluearchive");
  const [showPrompt, setShowPrompt] = useState(false);
  const [promptResult, setPromptResult] = useState<PreviewResult | null>(null);
  const [promptBusy, setPromptBusy] = useState(false);
  const [promptError, setPromptError] = useState("");
  const stream = useTranslateStream();
  const presets = useQuery({ queryKey: ["presets"], queryFn: getPresets });

  async function openPrompt() {
    if (!source.trim()) return;
    setShowPrompt(true);
    setPromptBusy(true);
    setPromptError("");
    try {
      const result = await preview({ source, preset });
      // Prefer messages captured from the last translate stream when present.
      setPromptResult(
        stream.messages ? { ...result, messages: stream.messages } : result
      );
    } catch (cause) {
      setPromptError(cause instanceof Error ? cause.message : "Preview failed");
    } finally {
      setPromptBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Translate"
        detail="Translate a passage with only the glossary terms that appear in this request."
      />
      <section className="workspace-grid">
        <div className="panel editor-panel">
          <div className="panel-head">
            <span>Source text</span>
            <span className="language-tag">Japanese</span>
          </div>
          <textarea
            value={source}
            onChange={(event) => setSource(event.target.value)}
            placeholder="Paste Japanese dialogue or prose here..."
          />
          <div className="toolbar">
            <label>
              Preset{" "}
              <select value={preset} onChange={(event) => setPreset(event.target.value)}>
                {presets.data?.presets.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                )) ?? <option value="bluearchive">Blue Archive</option>}
              </select>
            </label>
            <button
              className="primary"
              disabled={stream.busy || !source.trim()}
              onClick={() => void stream.run({ source, preset })}
            >
              {stream.busy ? "Translating..." : "Translate"}
            </button>
          </div>
          {stream.error && <p className="error">{stream.error}</p>}
        </div>
        <div className="panel output-panel">
          <div className="panel-head">
            <span>Translation</span>
            <span className="language-tag">Korean</span>
          </div>
          <div className="output-text">
            {stream.output || (
              <span className="placeholder">Your translation will appear here.</span>
            )}
          </div>
        </div>
      </section>
      <section className="lower-grid">
        <AppliedGlossary detected={stream.detected} />
        <div className="panel action-panel">
          <div>
            <p className="eyebrow">PROMPT CONTROL</p>
            <h2>이번 요청 Prompt 보기</h2>
            <p className="muted">
              Review the exact messages and token count assembled for this request.
            </p>
          </div>
          <button disabled={!source.trim()} onClick={() => void openPrompt()}>
            {showPrompt ? "Refresh prompt" : "View prompt"}
          </button>
        </div>
      </section>
      {showPrompt && (
        <section className="prompt-inline">
          <PageHeader title="이번 요청 Prompt" detail="Exact assembled messages for the current source and preset." />
          <PromptPreviewPanel
            result={promptResult}
            loading={promptBusy}
            error={promptError}
          />
        </section>
      )}
    </>
  );
}
