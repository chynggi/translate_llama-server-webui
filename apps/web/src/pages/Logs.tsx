import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getLogs } from "../api/logs";
import { PageHeader } from "../components/layout/Sidebar";

export function Logs() {
  const [offset, setOffset] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const limit = 20;
  const data = useQuery({
    queryKey: ["logs", limit, offset],
    queryFn: () => getLogs(limit, offset),
  });
  const total = data.data?.total ?? 0;
  const items = data.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Logs"
        detail="Recent translation requests and their applied terminology."
      />
      <div className="log-list">
        {items.map((item) => {
          const open = expanded === item.id;
          return (
            <article className="panel log-row" key={item.id}>
              <div>
                <strong>{item.preset}</strong>
                <span className="muted"> {new Date(item.ts).toLocaleString()}</span>
                <p>{item.source}</p>
                <button
                  className="linkish"
                  onClick={() => setExpanded(open ? null : item.id)}
                >
                  {open ? "Hide details" : "Expand"}
                </button>
                {open && (
                  <div className="log-details">
                    <div className="stat">
                      <span>Glossary matches</span>
                      <strong>{item.detected.total}</strong>
                    </div>
                    <h3>Prompt</h3>
                    {item.prompt.map((message, index) => (
                      <pre key={`${item.id}-${index}`} className="log-pre">
                        [{message.role}]{"\n"}
                        {message.content}
                      </pre>
                    ))}
                    <h3>Raw output</h3>
                    <pre className="log-pre">{item.raw_output}</pre>
                  </div>
                )}
              </div>
              <div>
                <b>{item.output}</b>
                <small>{item.detected.total} glossary matches</small>
              </div>
            </article>
          );
        })}
      </div>
      <div className="pager">
        <button disabled={offset <= 0} onClick={() => setOffset(Math.max(0, offset - limit))}>
          Previous
        </button>
        <span className="muted">
          {total === 0 ? "0" : `${offset + 1}–${Math.min(offset + limit, total)}`} of {total}
        </span>
        <button
          disabled={offset + limit >= total}
          onClick={() => setOffset(offset + limit)}
        >
          Next
        </button>
      </div>
    </>
  );
}
