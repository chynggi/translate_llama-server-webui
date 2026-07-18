# Translation Studio — Middleware

FastAPI middleware that sits between the web UI and llama.cpp. It is an
OpenAI-compatible proxy that adds glossary injection, prompt assembly, presets,
streaming, post-processing, and translation logging. llama.cpp is never
modified — the middleware only calls its HTTP API.

## Setup

```bash
cd apps/middleware
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Configuration lives in the repo-root `config/config.yaml` (llama-server URL,
paths, detector options, CORS). Environment overrides use the `TS_` prefix,
e.g. `TS_LLAMA_SERVER__BASE_URL=http://127.0.0.1:8080`.

## Run

```bash
uvicorn translator_studio.main:app --reload --host 127.0.0.1 --port 8000
```

Requires a running `llama-server` (default `http://127.0.0.1:8080`) for
`/translate`, `/preview` token counts, and the `/v1/*` proxy.

## Test

```bash
pytest
```

Unit tests mock the llama client, so no llama-server is needed.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/models` | Passthrough to llama-server |
| POST | `/v1/chat/completions` | Streaming passthrough (optional `preset` enrichment) |
| POST | `/translate` | Full pipeline, SSE when `stream: true` |
| POST | `/preview` | Assembled prompt + detected glossary + token count |
| GET | `/presets`, `/presets/{id}` | List / fetch presets |
| GET | `/glossary` | Search glossary (`?q=`, `?category=`) |
| GET | `/glossary/export` | Download glossary as YAML |
| POST | `/glossary` | `{action: "upsert" \| "import", ...}` |
| GET | `/logs` | Translation logs (paginated) |
| GET | `/settings` | Runtime llama-server + detector settings |
| PUT | `/settings` | Update runtime settings (optional YAML persist) |
