# Translation Studio

A desktop-first Japanese→Korean translation environment built around llama.cpp,
with a glassy chat UI, llama.app-compatible conversation trees, and full
llama.cpp sampler controls.

llama.cpp is never modified. All translation logic lives in a FastAPI
middleware that behaves as an OpenAI-compatible proxy. The React frontend talks
only to the middleware; the middleware talks only to llama.cpp.

```
Browser ──► React UI ──► FastAPI middleware ──► llama-server ──► GGUF model
                              │
   glossary · prompt builder · detector · postprocess · logs · conversations
```

## Features

- **Glassy chat UI** — design tokens ported from the llama.cpp glassy-modernui
  fork (oklch palettes, glassmorphism, glow, 8 theme styles, 7 accent colors,
  light/dark/system). Tailwind CSS 4.
- **llama.app conversation trees** — branching chats with sibling navigation
  (◀ 1/3 ▶), edit-to-fork, regenerate, reasoning ("thinking") blocks, and
  per-message token/speed stats. Import & export the exact llama.app JSONL
  format (loss-free round-trip verified across 58 real exports).
- **llama-server sampler controls** — 18 llama.cpp sampling parameters
  (temperature, top_k/p, min_p, dynatemp, xtc, repeat_penalty, dry_*, …)
  configurable from the Settings page and merged into every request.
- OpenAI-compatible proxy (`/v1/models`, `/v1/chat/completions`)
- Streaming translation (`/translate`) with reasoning + timings capture
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
   make middleware
   ```
3. Install and run the web UI:
   ```bash
   make web
   ```
4. Open http://localhost:5173

Run middleware tests (no llama-server required):

```bash
make test
```

## Layout

- `apps/web` — React + TypeScript + Tailwind 4 frontend (Vite)
- `apps/middleware` — FastAPI backend
- `glossary/` — YAML glossary files (categories are top-level keys; add freely)
- `presets/` — YAML translation presets
- `prompts/` — prompt templates (`system.md` = translation rules,
  `chat_system.md` = default chat system prompt)
- `conversations/` — llama.app-compatible JSONL chat history (created at runtime)
- `config/config.yaml` — middleware configuration (llama-server, detector,
  generation samplers, chat behaviour)
- `logs/` — translation logs (JSONL, created at runtime)

See `apps/middleware/README.md` for API details.
