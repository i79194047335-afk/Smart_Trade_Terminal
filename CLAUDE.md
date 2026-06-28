# CLAUDE.md — Smart Trade Terminal

> This file is read by the agent (Claude Code) at the start of every session. Keep it at the repository root. Update it as the project grows.

## What this is
A web trading terminal: charting (KLineChart), multi-source market data (forex/crypto/stocks/metals), backtesting, multi-window layouts, an economic calendar, and a trading journal. Monorepo. Goal: TradingView-class functionality on an open-source stack.

## Language
All documentation, code comments, identifiers, commit messages, and instruction files MUST be written in English. Conversation with the maintainer may happen in another language, but everything committed to the repository is in English.

## Project documents (read every session)
- **ROADMAP.md** — the single source of truth for scope and sequence. Every task maps to a step ID (e.g. `P1-S2`).
- **CHECKLIST.md** — live progress; mirrors ROADMAP step IDs exactly. Updated after each completed step.
- **CLAUDE.md** — this file: engineering rules and conventions.

## Workflow & governance (MANDATORY)
1. Before starting any task, find its step ID in `ROADMAP.md`. If the task is not a step there, **do not start it** — raise it with the maintainer first.
2. **No work outside the roadmap.** New ideas or deviations from the plan: stop, ask the maintainer for clarification, then update `ROADMAP.md` and `CHECKLIST.md` (same step IDs) **before** writing any code.
3. After completing a step: mark it `[x]` in `CHECKLIST.md` and record any follow-ups in `ROADMAP.md`.
4. Respect ⚠️ **NEEDS-SPEC** markers — those steps are under-specified and must be clarified with the maintainer before implementation.
5. One step at a time; one Pull Request per step. Keep the two documents in sync at all times.

## Stack
- **Frontend:** React + Vite + TypeScript + KLineChart. Package manager: pnpm.
- **Backend:** Python 3.12 + FastAPI + uvicorn. Env/package manager: uv.
- **Orchestration:** Docker + docker-compose.
- **Environment:** Ubuntu 22.04 VPS. Development via VSCode Remote-SSH on the server; production runs the same compose stack.
- **Agent:** Claude Code. Model routing — Claude for judgment-heavy work (architecture, candle-engine port, tricky debugging, security); DeepSeek v4 for mechanical work (boilerplate, configs, repetitive code) where CI gates fully catch errors.

## Commands
Backend (from `./backend`):
- `uv sync` — install dependencies
- `uv run uvicorn app.main:app --reload` — run the API (serves on `http://localhost:8000`)
- `uv run pytest` — tests
- `uv run pytest tests/test_health.py::test_health` — run one test (path::name, or `-k <expr>` to filter)
- `uv run ruff check .` — linter
- `uv run mypy app` — type checking

Frontend (from `./frontend`):
- `pnpm install`
- `pnpm dev` — dev server (serves on `http://localhost:5173`)
- `pnpm test` — tests (vitest)
- `pnpm test src/__tests__/smoke.test.ts` — run one test file (or `pnpm vitest run -t "<name>"` for one case)
- `pnpm typecheck` — type checking
- `pnpm build` — production build

Everything at once: `docker compose up --build` (backend on `:8000`, frontend on `:5173`).

## Architecture rules (strict)
1. **Chart layer is abstracted.** The UI never calls KLineChart directly — only through a `ChartEngine` wrapper. The engine must be replaceable.
2. **Data layer = adapters behind one interface.** Every source (Binance, FXCM/ForexConnect, Twelve Data, Finnhub) implements a common `DataSource` interface. The active provider is interchangeable and invisible to the rest of the code.
3. **Candle engine is pure and source-agnostic.** The `backend/app/candles/` module takes ticks/bars as input and outputs OHLC per timeframe. It must not know about brokers, networking, or WebSockets. No provider imports inside it.
4. **Layer separation:** FastAPI/WebSocket ← candle engine (pure) ← data-source adapters. Do not mix.
5. **Front/back contracts are fixed** via an OpenAPI schema; frontend types are generated from it, not written twice by hand.

## Definition of Done (every task, no exceptions)
- Backend green: `ruff check .` + `mypy app` + `pytest`.
- Frontend green: `pnpm typecheck` + `pnpm test` + `pnpm build`.
- Work on a feature branch, merge via Pull Request. The `main` branch is protected — no direct pushes.
- New logic is covered by tests. Without tests, the task is not done.

## Handle with care (do NOT "improve" without an explicit request)
- The candle-building and timeframe-aggregation logic is ported from a working `server.py` and contains deliberate nuances. Specifically: for timeframes ≥ M1 the new candle's *open* equals the previous candle's *close* (continuous candles), while for sub-minute timeframes (S5–S30) the *open* equals the current price. This behavior must be preserved exactly and locked down with tests. Change it only on an explicit human instruction, never on your own initiative.
- The timeframe list and the direct loading of H4/D1 (from broker history rather than aggregation) — preserve the logic and the reasoning (see comments in the source).

## Secrets and security (layered — all layers required)
- **Never hardcode** logins, passwords, or API keys. All secrets come from the environment.
- `.env` (real values) is git-ignored. Commit `.env.example` with variable NAMES and placeholder values only.
- Backend reads secrets via pydantic-settings. **Frontend note:** Vite inlines `VITE_*` variables into the client bundle, so they are PUBLIC — data-provider API keys (Twelve Data, Finnhub, etc.) live ONLY on the backend; the frontend calls the backend, never a provider directly with a key.
- **Local guard:** gitleaks runs as a pre-commit hook (via the pre-commit framework) and blocks commits containing secrets.
- **Server guard:** GitHub push protection is enabled on the repository (blocks recognized provider tokens before they reach the remote).
- **CI guard:** a gitleaks job runs on every Pull Request.
- **If a secret leaks:** rotate/revoke it immediately (a secret in a public repo is compromised within seconds), THEN purge history with `git filter-repo` or BFG. Rotation first — deleting the commit is not enough.

## Style and process
- Python: full type annotations, ruff formatting. TypeScript: strict mode.
- Small, modular PRs — one task at a time. Decompose large tasks.
- Consult this file before starting a task; if requirements conflict, ask the human.

## Code comments policy (MANDATORY — maintainer is non-programmer)
- Every non-trivial code block, function, and configuration file gets an explanatory comment in English.
- Comments explain **what** the block does and **why**, not just paraphrase the code.
- For files (Python modules, config files): a short header comment describing the file's purpose.
- For functions: a docstring (Python) or JSDoc/TSDoc (TS) covering purpose, parameters, and return value.
- Keep comments concise and accurate. Update them when the code changes — stale comments are worse than none.

## Repository layout
```
frontend/        React + Vite + TS + KLineChart
backend/
  app/
    main.py      FastAPI entry point
    data/        data-source adapters (DataSource): binance, fxcm, ...
    candles/     PURE candle & timeframe engine (ported from server.py)
  tests/
shared/          shared contracts (types generated from OpenAPI)
docker-compose.yml
.github/workflows/ci.yml   deterministic gates (lint / types / tests / build)
ROADMAP.md       scope & sequence (source of truth)
CHECKLIST.md     live progress (mirrors roadmap IDs)
```
