import { usePrefs } from "../../theme/prefs";

interface Props {
  reasoning: string;
  inProgress?: boolean;
}

/** Collapsible reasoning ("thinking") block, llama webui style. */
export function ThinkingBlock({ reasoning, inProgress = false }: Props) {
  const { prefs } = usePrefs();
  if (!reasoning && !inProgress) return null;
  return (
    <details
      className={`thinking-block${inProgress ? " in-progress" : ""}`}
      open={prefs.autoExpandThinking || inProgress}
    >
      <summary>{inProgress ? "사고하는 중…" : "사고 과정"}</summary>
      <div className="thinking-content">{reasoning}</div>
    </details>
  );
}
