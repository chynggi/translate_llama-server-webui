import type { PreviewResult } from "../../types";

interface Props {
  result: PreviewResult | null;
  loading?: boolean;
  error?: string;
  emptyHint?: string;
}

/** Shared prompt inspector used on Chat and the Prompt Preview page. */
export function PromptPreviewPanel({
  result,
  loading = false,
  error = "",
  emptyHint = "Assemble a prompt to inspect the exact messages sent to llama-server.",
}: Props) {
  if (loading) {
    return (
      <div className="panel prompt-panel">
        <p className="muted">Assembling prompt…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="panel prompt-panel">
        <p className="error">{error}</p>
      </div>
    );
  }
  if (!result) {
    return (
      <div className="panel prompt-panel">
        <p className="muted">{emptyHint}</p>
      </div>
    );
  }
  return (
    <div className="prompt-result">
      <div className="stat">
        <span>Token count</span>
        <strong>{result.token_count}</strong>
      </div>
      {result.messages.map((message, index) => (
        <article className="panel message" key={`${message.role}-${index}`}>
          <div className="message-role">{message.role}</div>
          <pre>{message.content}</pre>
        </article>
      ))}
    </div>
  );
}
