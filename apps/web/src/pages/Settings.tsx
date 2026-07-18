import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { getBaseUrl, setBaseUrl } from "../api/client";
import { getSettings, updateSettings } from "../api/settings";
import { PageHeader } from "../components/layout/Sidebar";

export function Settings() {
  const client = useQueryClient();
  const [middlewareUrl, setMiddlewareUrl] = useState(getBaseUrl());
  const [middlewareSaved, setMiddlewareSaved] = useState(false);
  const settings = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const [llamaUrl, setLlamaUrl] = useState("");
  const [defaultModel, setDefaultModel] = useState("");
  const [minAlias, setMinAlias] = useState(2);
  const [longestFirst, setLongestFirst] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!settings.data) return;
    setLlamaUrl(settings.data.llama_server.base_url);
    setDefaultModel(settings.data.llama_server.default_model);
    setMinAlias(settings.data.detector.min_alias_length);
    setLongestFirst(settings.data.detector.longest_match_first);
  }, [settings.data]);

  const save = useMutation({
    mutationFn: () =>
      updateSettings({
        llama_server: {
          base_url: llamaUrl,
          default_model: defaultModel,
        },
        detector: {
          min_alias_length: minAlias,
          longest_match_first: longestFirst,
        },
        persist: true,
      }),
    onSuccess: async () => {
      setMessage("Settings saved.");
      await client.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (cause) => {
      setMessage(cause instanceof Error ? cause.message : "Save failed");
    },
  });

  return (
    <>
      <PageHeader
        title="Settings"
        detail="Configure llama-server, detector options, and the middleware endpoint."
      />
      <section className="panel settings-panel">
        <h2>Middleware (browser)</h2>
        <label>
          Middleware URL
          <input
            value={middlewareUrl}
            onChange={(event) => {
              setMiddlewareUrl(event.target.value);
              setMiddlewareSaved(false);
            }}
            placeholder="http://127.0.0.1:8000"
          />
        </label>
        <button
          onClick={() => {
            setBaseUrl(middlewareUrl);
            setMiddlewareSaved(true);
          }}
        >
          {middlewareSaved ? "Saved" : "Save middleware URL"}
        </button>
        <p className="muted">Leave empty when using the Vite development proxy.</p>

        <hr />
        <h2>llama-server</h2>
        <label>
          Base URL
          <input
            value={llamaUrl}
            onChange={(event) => setLlamaUrl(event.target.value)}
            placeholder="http://127.0.0.1:8080"
          />
        </label>
        <label>
          Default model
          <input
            value={defaultModel}
            onChange={(event) => setDefaultModel(event.target.value)}
            placeholder="optional model id"
          />
        </label>

        <h2>Detector</h2>
        <label>
          Minimum alias length
          <input
            type="number"
            min={1}
            value={minAlias}
            onChange={(event) => setMinAlias(Number(event.target.value))}
          />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={longestFirst}
            onChange={(event) => setLongestFirst(event.target.checked)}
          />
          Longest-match-first
        </label>

        <button
          className="primary"
          disabled={save.isPending || settings.isLoading}
          onClick={() => save.mutate()}
        >
          {save.isPending ? "Saving..." : "Save server settings"}
        </button>
        {message && <p className="muted">{message}</p>}
      </section>
    </>
  );
}
