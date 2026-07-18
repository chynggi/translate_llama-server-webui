import type { DetectedGlossary } from "../../types";
import { entriesByCategory, matchCount } from "../../utils/glossaryGroup";

export function AppliedGlossary({ detected }: { detected: DetectedGlossary | null }) {
  const categories = detected ? entriesByCategory(detected) : [];
  return (
    <div className="panel applied">
      <div className="panel-head">
        <span>Applied glossary</span>
        <strong>{detected ? matchCount(detected) : 0} matches</strong>
      </div>
      {!detected && (
        <p className="muted">Terms detected in your latest request will be listed here.</p>
      )}
      {categories.map(([category, entries]) => (
        <div className="term-group" key={category}>
          <div className="term-category">{category}</div>
          {entries.map((entry) => (
            <div className="term" key={entry.source}>
              <span>{entry.source}</span>
              <b>{entry.ko}</b>
              <small>{entry.occurrences}x</small>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
