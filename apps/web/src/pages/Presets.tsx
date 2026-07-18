import { useQuery } from "@tanstack/react-query";
import { getPresets } from "../api/presets";
import { PageHeader } from "../components/layout/Sidebar";

export function Presets() {
  const data = useQuery({ queryKey: ["presets"], queryFn: getPresets });
  return (
    <>
      <PageHeader
        title="Presets"
        detail="Reusable translation instructions and model parameters."
      />
      <div className="card-list">
        {data.data?.presets.map((item) => (
          <article className="panel preset-card" key={item.id}>
            <div>
              <p className="eyebrow">{item.id}</p>
              <h2>{item.name}</h2>
              <p className="muted">{item.description}</p>
            </div>
            <dl>
              <dt>Style</dt>
              <dd>{item.style || "Default"}</dd>
              <dt>Model</dt>
              <dd>{item.model || "Server default"}</dd>
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}
