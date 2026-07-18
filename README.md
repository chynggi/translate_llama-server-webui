# Translation Studio

A desktop-first Japanese→Korean translation environment built around llama.cpp.

llama.cpp is never modified. All translation logic lives in a FastAPI
middleware that behaves as an OpenAI-compatible proxy. The React frontend talks
only to the middleware; the middleware talks only to llama.cpp.

```
Browser ──► React UI ──► FastAPI middleware ──► llama-server ──► GGUF model
                              │
              glossary · prompt builder · detector · postprocess · logs
```

## Features (MVP)

- OpenAI-compatible proxy (`/v1/models`, `/v1/chat/completions`)
- Streaming translation (`/translate`)
- Glossary engine with automatic term detection (only used terms are injected)
- Prompt builder with a fixed, inspectable order + always-available prompt preview
- Presets, YAML glossary import/export, translation logs

## Quick start

1. Start llama.cpp's server with any GGUF model:
   ```bash
   llama-server -m model.gguf --port 8080
   ```
2. Install and run the middleware:
   ```bash
   make middleware        # or: cd apps/middleware && pip install -e ".[dev]" && uvicorn translator_studio.main:app --reload
   ```
3. Install and run the web UI:
   ```bash
   make web               # or: cd apps/web && npm install && npm run dev
   ```
4. Open http://localhost:5173

Run middleware tests (no llama-server required):

```bash
make test
```

## Layout

- `apps/web` — React + TypeScript frontend (Vite)
- `apps/middleware` — FastAPI backend
- `glossary/` — YAML glossary files (categories are top-level keys; add freely)
- `presets/` — YAML translation presets
- `prompts/` — prompt templates (`system.md` is the active system rules)
- `config/config.yaml` — middleware configuration
- `logs/` — translation logs (JSONL, created at runtime)

See `apps/middleware/README.md` for API details.
