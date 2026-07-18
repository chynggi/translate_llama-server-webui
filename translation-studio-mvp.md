# Translation Studio — MVP Implementation Plan

A desktop-first Japanese→Korean translation environment around llama.cpp. llama.cpp is **never touched**; all translation logic lives in a FastAPI middleware that behaves as an OpenAI-compatible proxy. The frontend talks only to the middleware.

## Guiding principles (override default agent behavior)

- **Translation quality > UI polish.** When in conflict, choose accuracy.
- **Glossary accuracy > new features.** Never add features that don't directly serve the translation workflow.
- **Maintainability > Extensibility > Simplicity > Performance > UI polish.**
- No business logic in UI components. No coupling between translation logic and frontend.
- Small modules, **100–300 LOC per file**, dependency injection, no global state unless necessary.
- Business logic (glossary, detector, prompt builder, postprocess) must be **unit-testable without UI and without llama-server** (via mocks).
- Don't implement features outside MVP scope.

## Tech stack (confirmed)

| Layer | Choice |
|---|---|
| Middleware | FastAPI + Pydantic + Pydantic-Settings (Python 3.11+) |
| Frontend | Vite + React + TypeScript + React Router v6 |
| Data | YAML glossary/preset files, JSON logs |
| llama.cpp | External `llama-server`, default `http://localhost:8080`, configurable |
| Token counting | llama-server `POST /tokenize` (exact, model-matched) |
| HTTP client (server) | httpx (async, streaming) |
| Server state (frontend) | TanStack Query |
| Local UI state (frontend) | Minimal React state / tiny Zustand store only if needed |
| Tests | pytest (backend), Vitest (frontend utilities) |

## Repository structure

Honor the user's proposed layout. Data dirs at repo root; code under `apps/`.

```
/home/chynggi/translate_llama-server-webui/
├── apps/
│   ├── web/                      # Vite + React + TS frontend
│   └── middleware/               # FastAPI backend
├── glossary/                     # YAML glossary files (data)
│   └── bluearchive.yaml
├── presets/                      # YAML preset files (data)
│   └── bluearchive.yaml
├── prompts/                      # prompt templates (data)
│   ├── system.md
│   ├── translation.md
│   └── proofreading.md
├── config/
│   └── config.yaml
├── logs/                         # translation logs (JSONL), created at runtime
├── cache/                        # reserved for 2.0 TM
├── plugins/                      # reserved for 2.0
├── tests/                        # root-level integration tests (optional)
├── Makefile                      # run both servers (convenience)
└── README.md
```

## Middleware architecture (`apps/middleware/`)

```
apps/middleware/
├── pyproject.toml
├── README.md
├── src/translator_studio/
│   ├── main.py              # FastAPI app factory + lifespan (builds service container), CORS, router wiring
│   ├── config.py            # pydantic-settings: llama_server URL, paths, detector opts, server/cors
│   ├── container.py         # Services dataclass — the DI root, constructed in lifespan, accessed via Depends
│   ├── api/
│   │   ├── router.py        # aggregate all sub-routers under /v1 and root
│   │   ├── deps.py          # FastAPI Depends() providers exposing Services to routes
│   │   ├── schemas.py       # OpenAI-compatible + translate/preview request/response models
│   │   ├── openai_proxy.py  # GET /v1/models, POST /v1/chat/completions (streaming passthrough + optional enrichment)
│   │   ├── translate.py     # POST /translate (full pipeline, SSE)
│   │   ├── preview.py       # POST /preview (assembled prompt + breakdown + token count)
│   │   ├── presets.py       # GET /presets, GET /presets/{id}
│   │   ├── glossary.py      # GET /glossary (search/filter), POST /glossary (upsert + YAML import)
│   │   └── logs.py          # GET /logs (paginated, expandable)
│   ├── glossary/
│   │   ├── models.py        # GlossaryEntry, GlossaryCategory, Glossary (pydantic)
│   │   ├── loader.py        # read+merge all YAML in glossary dir → Glossary (category = top-level key)
│   │   ├── repository.py    # in-memory store with CRUD + YAML import/export + file persistence
│   │   └── service.py       # high-level ops consumed by detector & api
│   ├── detector/
│   │   ├── matcher.py       # core: longest-match-first substring + alias matching + span tracking
│   │   └── service.py       # detect(source, glossary) → DetectedGlossary (per category, only matched)
│   ├── prompt/
│   │   ├── models.py        # Preset, PromptParts, AssembledPrompt
│   │   ├── templates.py     # load prompts/*.md
│   │   ├── presets.py       # load presets/*.yaml
│   │   └── builder.py       # assemble messages in fixed order (see Prompt Builder)
│   ├── translation/
│   │   ├── llama_client.py  # async httpx client: /v1/models, /v1/chat/completions (stream), /tokenize
│   │   ├── streamer.py      # SSE chunk parsing + passthrough + final-event emission
│   │   └── service.py       # orchestrates detect → build → call llama → postprocess → log
│   ├── postprocess/
│   │   └── service.py       # MVP: trim, strip code fences/markup; extensible pipeline
│   ├── logs/
│   │   └── logger.py        # append JSONL: source, preset, detected glossary, prompt, raw output, final
│   └── utils/
│       ├── yaml_io.py       # read/write YAML (ruamel.yaml to preserve comments on write)
│       └── tokens.py        # count tokens via llama-server /tokenize; graceful fallback to char estimate
└── tests/
    ├── conftest.py          # fixtures: sample glossary, sample source, mocked llama_client
    ├── test_glossary_loader.py
    ├── test_glossary_repository.py
    ├── test_detector_matcher.py
    ├── test_prompt_builder.py
    ├── test_prompt_presets.py
    ├── test_translation_service.py
    ├── test_postprocess.py
    ├── test_api_translate.py
    ├── test_api_preview.py
    └── test_utils_tokens.py
```

Dependency injection: `container.py` builds a `Services` dataclass once at startup (glossary_service, detector_service, prompt_builder, llama_client, translation_service, postprocessor, logger). Routes receive what they need via `deps.py` `Depends()` providers. No service locator, no framework.

## Glossary Engine (most important module — design in detail)

**YAML format** (category = top-level key; new categories need **zero code changes**):
```yaml
students:
  空崎ヒナ:
    ko: 소라사키 히나
    aliases: ["ヒナ"]        # source-language alternate forms (also trigger detection)
  陸八魔アル:
    ko: 리쿠하치마 아루
    aliases: ["アル"]
locations:
  ゲヘナ:
    ko: 게헨나
organizations:
  便利屋68:
    ko: 흥신소68
```

- A glossary **file** may contain multiple **categories** (top-level keys). The loader merges every `*.yaml` in `glossary/` into one in-memory `Glossary`. Drop in a new file or add a top-level key → new category, no code change. `aliases.yaml` / `ui.yaml` / future files are just more glossary files.
- Each entry: `source_term: { ko: str, aliases: [str] }`. `ko` is the canonical Korean rendering injected into the prompt. `aliases` are **source-language** surface forms that also match during detection (e.g. `ヒナ` for `空崎ヒナ`).
- The engine never special-cases category names; categories are pure data.

**Detection algorithm** (`detector/matcher.py`):
1. Collect all (entry, alias-or-term) match surfaces across the active glossary.
2. Sort by length **descending** (longest-match-first) so `空崎ヒナ` wins over `ヒナ`.
3. Scan the source text; record matched spans. Skip candidate matches that overlap an already-claimed span (prevents double injection / sub-term collisions).
4. Guard against short-alias false positives via `detector.min_alias_length` (default 2) from config.
5. Return `DetectedGlossary`: per-category list of matched entries only.

**Injection rule**: only matched entries are injected, grouped by category, formatted as:
```
Glossary
空崎ヒナ = 소라사키 히나
陸八魔アル = 리쿠하치마 아루
```
Never inject the whole glossary.

## Prompt Builder (fixed order)

`builder.py` produces OpenAI chat `messages`:

```
messages = [
  {role: "system", content:
    1. System Rules   (prompts/system.md + preset.system_rules)
    2. Preset         (preset.style / tone / instructions)
    3. Detected Glossary (only matched entries)
  },
  {role: "user", content:
    4. User Instruction (preset.user_instruction or request override)
    5. Source Text
  }
]
```

- `POST /preview` returns `{ messages, parts: {system_rules, preset, glossary, user_instruction, source}, detected: {category: [entries]}, token_count }`.
- Prompt preview is always available — both as a standalone page and as the "이번 요청 Prompt 보기" panel on the Chat page.

## API contract

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/models` | Passthrough to llama-server. |
| POST | `/v1/chat/completions` | Streaming passthrough; if body includes `preset`, run detect→build→enrich first; else pure passthrough. |
| POST | `/translate` | Full pipeline: `{source, preset, glossary_set?, project?, stream?}` → detect → build → llama-server (stream) → postprocess → log. SSE response. |
| POST | `/preview` | `{source, preset}` → assembled prompt + detected glossary + token count (no LLM call). |
| GET | `/presets` | List presets; `GET /presets/{id}` for one. |
| GET | `/glossary` | List entries grouped by category; supports `?q=` search, `?category=`. |
| POST | `/glossary` | Upsert entry or import YAML (`{action: "import", yaml: "..."}` / `{action: "upsert", category, source, ko, aliases}`). |
| GET | `/logs` | Paginated translation logs. |

Streaming: FastAPI `StreamingResponse` + httpx async stream; SSE chunks forwarded to browser; a final `event: done` carries postprocessed text + detected glossary + token usage.

## Frontend architecture (`apps/web/`)

```
apps/web/
├── package.json
├── vite.config.ts
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx                 # router + layout
    ├── api/
    │   ├── client.ts           # typed fetch wrapper (baseURL from env)
    │   ├── translate.ts        # translate + SSE stream reader over fetch
    │   ├── glossary.ts
    │   ├── presets.ts
    │   ├── preview.ts
    │   └── logs.ts
    ├── components/
    │   ├── layout/Sidebar.tsx
    │   ├── glossary/...        # category tabs, search, entry list, edit form, import/export
    │   ├── prompt/PromptPreviewPanel.tsx   # reused on Chat + Prompt Preview page
    │   └── chat/...
    ├── pages/
    │   ├── Chat.tsx            # source input + streaming output + applied-glossary panel + "view prompt"
    │   ├── Projects.tsx        # STUB: "Coming in 2.0"
    │   ├── Glossary.tsx
    │   ├── Presets.tsx
    │   ├── PromptPreview.tsx
    │   ├── Logs.tsx
    │   └── Settings.tsx        # llama-server URL, default model, detector opts
    ├── hooks/
    │   ├── useTranslateStream.ts
    │   └── useGlossary.ts
    └── types/                  # shared TS types mirroring middleware schemas
```

- Desktop-first, simple, no fancy chat UI. Sidebar nav + main panel.
- TanStack Query for all server state; mutations for glossary upsert/import.
- Streaming over `fetch` + `ReadableStream` (SSE is POST, so not `EventSource`). Parse `data:` lines, render incrementally.
- **Applied-glossary panel** on Chat (the user's signature feature): after a request, show per-category matched terms with counts + total. "이번 요청 Prompt 보기" opens `PromptPreviewPanel` with the exact assembled prompt + token count.

## Milestones (each leaves the project runnable)

**M1 — Proxy**
- `config.py`, `container.py`, `main.py` (lifespan, CORS), `llama_client.py`, `api/openai_proxy.py` (`/v1/models`, `/v1/chat/completions` streaming passthrough).
- Root `config/config.yaml`, `Makefile`, `README.md` run instructions.
- Tests: `test_api_openai_proxy` with mocked llama_client.

**M2 — Prompt Builder**
- `prompt/templates.py`, `prompt/presets.py`, `prompt/builder.py`, `api/preview.py`, `utils/tokens.py`.
- Seed `prompts/*.md`, `presets/bluearchive.yaml`.
- Tests: `test_prompt_builder` (order + only-matched glossary injection), `test_prompt_presets`, `test_utils_tokens` (mocked /tokenize).

**M3 — Glossary Engine**
- `glossary/{models,loader,repository,service}.py`, `detector/{matcher,service}.py`, `api/glossary.py`.
- Seed `glossary/bluearchive.yaml` using the user's example entries.
- Tests: `test_glossary_loader`, `test_glossary_repository`, `test_detector_matcher` (longest-match, alias, span de-overlap, min-length guard, no false positives).

**M4 — Streaming translation pipeline**
- `translation/{service,streamer}.py`, `postprocess/service.py`, `logs/logger.py`, `api/translate.py`, `api/logs.py`.
- Tests: `test_translation_service` (mocked llama_client: detect→build→call→postprocess→log), `test_postprocess`, `test_api_translate` (TestClient SSE).

**M5 — Frontend**
- Vite scaffold, router, Sidebar, all 7 pages, API client + SSE reader, `PromptPreviewPanel`, applied-glossary panel, Settings.
- Vitest for SSE parser + glossary grouping helpers.
- End-to-end manual verification against a running llama-server.

**Out of scope (post-MVP, do not build):** Translation Memory / cache logic (M6), QA (M7), project management, character speech-style auto-apply, postprocess auto-correction beyond trivial cleanup, terminology conflict detection, multi-model compare, diff viewer, Git-based glossary versioning, auth, cloud sync, plugins, themes, AI agent, workflow builder, voice, OCR, image translation. `cache/` and `plugins/` dirs are reserved only.

## Testing strategy

- **Backend core modules** (glossary, detector, prompt builder, postprocess, translation service) are pure-Python and tested with **mocked** `llama_client` — no llama-server required.
- API tests use FastAPI `TestClient` with the service container wired to mocks.
- **Detector** gets the most thorough tests (it's the quality-critical path): longest-match precedence, alias matching, overlap de-duplication, min-length guard, empty/whitespace source, no-match returns empty, multi-category.
- **Prompt builder** tests assert exact ordering and that only detected entries appear.
- Frontend: Vitest covers the SSE stream parser and glossary grouping helpers; component tests kept minimal (quality logic lives in middleware).

## Verification

1. `cd apps/middleware && uv sync && uv run pytest` — all unit/API tests green without llama-server.
2. Start a llama-server with any GGUF (e.g. `llama-server -m model.gguf --port 8080`).
3. `uv run uvicorn translator_studio.main:app --reload` → `GET http://127.0.0.1:8000/v1/models` returns model list.
4. `POST /preview` with sample Japanese + Blue Archive preset → confirm detected glossary (空崎ヒナ, 陸八魔アル) and token count.
5. `POST /translate` (stream) → streamed Korean output; applied-glossary panel + prompt preview match; entry appears in `GET /logs`.
6. `cd apps/web && npm install && npm run dev` → open Chat, run a translation, click "이번 요청 Prompt 보기", verify the exact prompt + token count + matched terms.
7. Glossary page: search, edit an entry, import YAML, confirm it persists to `glossary/*.yaml` and is detected on next translate.
