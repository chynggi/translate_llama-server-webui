import type { MessageTimings } from "../../types";

function fmt(value: number | undefined, digits = 1): string {
  if (value === undefined || Number.isNaN(value)) return "-";
  return value.toFixed(digits);
}

/** Per-message generation stats from llama.cpp `timings` (showMessageStats). */
export function MessageStats({ timings }: { timings: MessageTimings }) {
  const items: [string, string][] = [];
  if (timings.prompt_n !== undefined) {
    items.push(["prompt", `${timings.prompt_n} tok`]);
  }
  if (timings.cache_n) items.push(["cache", `${timings.cache_n} tok`]);
  if (timings.prompt_per_second !== undefined) {
    items.push(["prompt speed", `${fmt(timings.prompt_per_second)} t/s`]);
  }
  if (timings.predicted_n !== undefined) {
    items.push(["generated", `${timings.predicted_n} tok`]);
  }
  if (timings.predicted_per_second !== undefined) {
    items.push(["speed", `${fmt(timings.predicted_per_second)} t/s`]);
  }
  if (timings.predicted_ms !== undefined) {
    items.push(["time", `${fmt(timings.predicted_ms / 1000, 2)} s`]);
  }
  if (items.length === 0) return null;
  return (
    <div className="msg-stats">
      {items.map(([label, value]) => (
        <span key={label}>
          {label} <b>{value}</b>
        </span>
      ))}
    </div>
  );
}
