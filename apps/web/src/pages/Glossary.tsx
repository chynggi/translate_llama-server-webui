import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { exportYaml, importYaml, upsertEntry } from "../api/glossary";
import { PageHeader } from "../components/layout/Sidebar";
import { useGlossary } from "../hooks/useGlossary";

export function Glossary() {
  const client = useQueryClient();
  const { q, setQ, data } = useGlossary();
  const [yaml, setYaml] = useState("");
  const [form, setForm] = useState({
    category: "students",
    source: "",
    ko: "",
    aliases: "",
  });
  const [exportBusy, setExportBusy] = useState(false);

  async function save() {
    await upsertEntry({
      ...form,
      aliases: form.aliases
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    });
    setForm({ ...form, source: "", ko: "", aliases: "" });
    await client.invalidateQueries({ queryKey: ["glossary"] });
  }

  async function downloadExport() {
    setExportBusy(true);
    try {
      const text = await exportYaml();
      const blob = new Blob([text], { type: "application/x-yaml" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "glossary.yaml";
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Glossary"
        detail="Maintain canonical Korean renderings and source-language aliases."
      />
      <div className="split-layout">
        <section>
          <div className="search-row">
            <input
              value={q}
              onChange={(event) => setQ(event.target.value)}
              placeholder="Search terms or aliases"
            />
            <span className="count">{data?.total_entries ?? 0} entries</span>
            <button disabled={exportBusy} onClick={() => void downloadExport()}>
              {exportBusy ? "Exporting..." : "Export YAML"}
            </button>
          </div>
          {data?.categories.map((category) => (
            <div className="category-section" key={category.name}>
              <h2>{category.name}</h2>
              {category.entries.map((entry) => (
                <div className="term glossary-term" key={entry.source}>
                  <span>
                    {entry.source}
                    <small>{entry.aliases.join(", ")}</small>
                  </span>
                  <b>{entry.ko}</b>
                </div>
              ))}
            </div>
          ))}
        </section>
        <aside className="panel form-panel">
          <h2>Add entry</h2>
          <input
            placeholder="Category"
            value={form.category}
            onChange={(event) => setForm({ ...form, category: event.target.value })}
          />
          <input
            placeholder="Japanese source"
            value={form.source}
            onChange={(event) => setForm({ ...form, source: event.target.value })}
          />
          <input
            placeholder="Korean rendering"
            value={form.ko}
            onChange={(event) => setForm({ ...form, ko: event.target.value })}
          />
          <input
            placeholder="Aliases, comma separated"
            value={form.aliases}
            onChange={(event) => setForm({ ...form, aliases: event.target.value })}
          />
          <button
            className="primary"
            disabled={!form.source || !form.ko}
            onClick={() => void save()}
          >
            Save entry
          </button>
          <hr />
          <h2>Import YAML</h2>
          <textarea
            value={yaml}
            onChange={(event) => setYaml(event.target.value)}
            placeholder={"category:\n  source:\n    ko: rendering"}
          />
          <button
            disabled={!yaml.trim()}
            onClick={async () => {
              await importYaml(yaml);
              setYaml("");
              await client.invalidateQueries({ queryKey: ["glossary"] });
            }}
          >
            Import
          </button>
        </aside>
      </div>
    </>
  );
}
