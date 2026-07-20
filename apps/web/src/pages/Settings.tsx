import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { getBaseUrl, setBaseUrl } from "../api/client";
import { getSettings, updateSettings } from "../api/settings";
import type { GenerationValues } from "../api/settings";
import { PageHeader } from "../components/layout/Sidebar";
import { ACCENT_OPTIONS, THEME_STYLE_OPTIONS } from "../theme/accents";
import type { ChatWidthStyle, ThemeMode, ThemeStyle } from "../theme/accents";
import { usePrefs } from "../theme/prefs";

interface GenerationField {
  key: string;
  label: string;
  kind: "number" | "text";
  step?: string;
}

/** llama.cpp sampler fields, mirroring the llama webui userOverrides list. */
const GENERATION_FIELDS: GenerationField[] = [
  { key: "temperature", label: "temperature", kind: "number", step: "0.01" },
  { key: "dynatemp_range", label: "dynatemp_range", kind: "number", step: "0.01" },
  { key: "dynatemp_exponent", label: "dynatemp_exponent", kind: "number", step: "0.01" },
  { key: "top_k", label: "top_k", kind: "number", step: "1" },
  { key: "top_p", label: "top_p", kind: "number", step: "0.01" },
  { key: "min_p", label: "min_p", kind: "number", step: "0.001" },
  { key: "xtc_probability", label: "xtc_probability", kind: "number", step: "0.01" },
  { key: "xtc_threshold", label: "xtc_threshold", kind: "number", step: "0.01" },
  { key: "max_tokens", label: "max_tokens", kind: "number", step: "1" },
  { key: "samplers", label: "samplers (order)", kind: "text" },
  { key: "repeat_last_n", label: "repeat_last_n", kind: "number", step: "1" },
  { key: "repeat_penalty", label: "repeat_penalty", kind: "number", step: "0.01" },
  { key: "presence_penalty", label: "presence_penalty", kind: "number", step: "0.01" },
  { key: "frequency_penalty", label: "frequency_penalty", kind: "number", step: "0.01" },
  { key: "dry_multiplier", label: "dry_multiplier", kind: "number", step: "0.01" },
  { key: "dry_base", label: "dry_base", kind: "number", step: "0.01" },
  { key: "dry_allowed_length", label: "dry_allowed_length", kind: "number", step: "1" },
  { key: "dry_penalty_last_n", label: "dry_penalty_last_n", kind: "number", step: "1" },
];

export function Settings() {
  const client = useQueryClient();
  const { prefs, setPref } = usePrefs();
  const [middlewareUrl, setMiddlewareUrl] = useState(getBaseUrl());
  const [middlewareSaved, setMiddlewareSaved] = useState(false);
  const settings = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const [llamaUrl, setLlamaUrl] = useState("");
  const [defaultModel, setDefaultModel] = useState("");
  const [minAlias, setMinAlias] = useState(2);
  const [longestFirst, setLongestFirst] = useState(true);
  const [gen, setGen] = useState<Record<string, string>>({});
  const [enableThinking, setEnableThinking] = useState(false);
  const [excludeReasoning, setExcludeReasoning] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!settings.data) return;
    setLlamaUrl(settings.data.llama_server.base_url);
    setDefaultModel(settings.data.llama_server.default_model);
    setMinAlias(settings.data.detector.min_alias_length);
    setLongestFirst(settings.data.detector.longest_match_first);
    setEnableThinking(settings.data.chat.enable_thinking);
    setExcludeReasoning(settings.data.chat.exclude_reasoning_from_context);
    const values: Record<string, string> = {};
    for (const field of GENERATION_FIELDS) {
      const value = settings.data.generation[field.key];
      values[field.key] = value === null || value === undefined ? "" : String(value);
    }
    setGen(values);
  }, [settings.data]);

  function generationPayload(): GenerationValues {
    const payload: GenerationValues = {};
    for (const field of GENERATION_FIELDS) {
      const raw = (gen[field.key] ?? "").trim();
      if (raw === "") {
        payload[field.key] = null;
      } else if (field.kind === "text") {
        payload[field.key] = raw;
      } else {
        const parsed = Number(raw);
        payload[field.key] = Number.isNaN(parsed) ? null : parsed;
      }
    }
    return payload;
  }

  const save = useMutation({
    mutationFn: () =>
      updateSettings({
        llama_server: { base_url: llamaUrl, default_model: defaultModel },
        detector: {
          min_alias_length: minAlias,
          longest_match_first: longestFirst,
        },
        generation: generationPayload(),
        chat: {
          enable_thinking: enableThinking,
          exclude_reasoning_from_context: excludeReasoning,
        },
        persist: true,
      }),
    onSuccess: async () => {
      setMessage("설정을 저장했습니다.");
      await client.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (cause) => {
      setMessage(cause instanceof Error ? cause.message : "저장 실패");
    },
  });

  return (
    <>
      <PageHeader
        title="Settings"
        detail="llama-server 연결, 생성 샘플러, 외관 테마와 채팅 동작을 설정합니다."
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
          {middlewareSaved ? "저장됨" : "Save middleware URL"}
        </button>
        <p className="muted">Vite 개발 프록시를 쓰는 경우 비워 두세요.</p>

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

        <hr />
        <h2>Generation (llama.cpp 샘플러)</h2>
        <p className="muted">
          비워 두면 해당 파라미터는 전송하지 않습니다. 서버 기본값으로 모든
          요청에 적용되며, 프리셋/개별 요청 값이 우선합니다.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
            gap: 12,
          }}
        >
          {GENERATION_FIELDS.map((field) => (
            <label key={field.key} style={{ fontWeight: 500, fontSize: 13 }}>
              {field.label}
              <input
                type={field.kind}
                step={field.step}
                value={gen[field.key] ?? ""}
                placeholder="unset"
                onChange={(event) =>
                  setGen((current) => ({
                    ...current,
                    [field.key]: event.target.value,
                  }))
                }
              />
            </label>
          ))}
        </div>

        <h2>Chat 동작 (서버)</h2>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableThinking}
            onChange={(event) => setEnableThinking(event.target.checked)}
          />
          enable_thinking — reasoning 파싱 활성화
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={excludeReasoning}
            onChange={(event) => setExcludeReasoning(event.target.checked)}
          />
          exclude_reasoning_from_context — 후속 요청 컨텍스트에서 사고 제외
        </label>

        <button
          className="primary"
          disabled={save.isPending || settings.isLoading}
          onClick={() => save.mutate()}
        >
          {save.isPending ? "저장 중…" : "서버 설정 저장"}
        </button>
        {message && <p className="muted">{message}</p>}
      </section>

      <section className="panel settings-panel" style={{ marginTop: 18 }}>
        <h2>Appearance (이 브라우저)</h2>
        <label>
          Theme
          <select
            value={prefs.theme}
            onChange={(event) => setPref("theme", event.target.value as ThemeMode)}
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
        <label>
          Theme style
          <select
            value={prefs.themeStyle}
            onChange={(event) =>
              setPref("themeStyle", event.target.value as ThemeStyle)
            }
          >
            {THEME_STYLE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Accent color
          <select
            value={prefs.accentColor}
            onChange={(event) => setPref("accentColor", event.target.value)}
          >
            {ACCENT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Chat width
          <select
            value={prefs.chatWidthStyle}
            onChange={(event) =>
              setPref("chatWidthStyle", event.target.value as ChatWidthStyle)
            }
          >
            <option value="default">Default (3xl)</option>
            <option value="wide">Wide (5xl)</option>
            <option value="full">Full</option>
          </select>
        </label>

        <h2>Chat 동작 (이 브라우저)</h2>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={prefs.sendOnEnter}
            onChange={(event) => setPref("sendOnEnter", event.target.checked)}
          />
          Enter로 전송 (Shift+Enter 줄바꿈)
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={prefs.showMessageStats}
            onChange={(event) => setPref("showMessageStats", event.target.checked)}
          />
          showMessageStats — 메시지별 토큰/속도 통계 표시
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={prefs.showThoughtInProgress}
            onChange={(event) =>
              setPref("showThoughtInProgress", event.target.checked)
            }
          />
          showThoughtInProgress — 생성 중 사고 블록 표시
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={prefs.autoExpandThinking}
            onChange={(event) => setPref("autoExpandThinking", event.target.checked)}
          />
          autoExpandThinking — 사고 블록 기본 펼침
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={prefs.renderUserContentAsMarkdown}
            onChange={(event) =>
              setPref("renderUserContentAsMarkdown", event.target.checked)
            }
          />
          renderUserContentAsMarkdown — 사용자 메시지도 마크다운 렌더링
        </label>
      </section>
    </>
  );
}
