import { useState } from "react";
import { preview } from "../api/preview";
import { PageHeader } from "../components/layout/Sidebar";
import { PromptPreviewPanel } from "../components/prompt/PromptPreviewPanel";
import type { PreviewResult } from "../types";

export function PromptPreview() {
  const params = new URLSearchParams(window.location.search);
  const [source, setSource] = useState(params.get("source") ?? "");
  const [preset, setPreset] = useState(params.get("preset") ?? "bluearchive");
  const [result, setResult] = useState<PreviewResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function inspect() {
    setBusy(true);
    setError("");
    try {
      setResult(await preview({ source, preset }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Preview failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Prompt preview"
        detail="See every message sent to llama-server before a translation request."
      />
      <div className="prompt-controls">
        <textarea
          value={source}
          onChange={(event) => setSource(event.target.value)}
          placeholder="Source text"
        />
        <div>
          <input value={preset} onChange={(event) => setPreset(event.target.value)} />
          <button
            className="primary"
            disabled={!source.trim() || busy}
            onClick={() => void inspect()}
          >
            {busy ? "Assembling..." : "Assemble prompt"}
          </button>
        </div>
      </div>
      <PromptPreviewPanel result={result} loading={busy} error={error} />
    </>
  );
}
