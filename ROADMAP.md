# Smart Trade Terminal — Roadmap

> **Single source of truth for scope and sequence.** Read together with `CHECKLIST.md` (live progress) and `CLAUDE.md` (engineering rules). Every unit of work must map to a step ID below. This document and the checklist are kept in sync at all times.

## 1. Project description
A web-based trading terminal aiming at TradingView-class functionality on an open-source stack: charting with drawing tools and indicators, multi-window layouts, backtesting, strategy/bot authoring, an economic calendar, a trading journal, and multiple asset classes (forex, crypto, stocks, metals) from free data sources at the start. Built as a monorepo, developed test-gated, reusing proven candle/timeframe logic from an existing `server.py`.

## 2. Goals
- **Primary:** a charting engine not inferior to TradingView in core functionality.
- Multi-source market data behind a single, interchangeable interface.
- Reproducible, test-gated development — deterministic CI as the quality gate, not an optional extra.
- Preserve and reuse the proven candle/timeframe engine from the existing `server.py`.

## 3. How these documents work — GOVERNANCE (read first)
- **This roadmap is the single source of truth** for what we build and in what order.
- **No work happens outside the roadmap.** If a task is not a step here, it does not get done yet.
- **Deviations and new ideas:** never implement silently. Stop, raise it with the maintainer, get clarification, then add or modify the relevant step(s) here **and** in `CHECKLIST.md` *before* coding.
- **After completing a step:** tick it in `CHECKLIST.md` and record any follow-ups here.
- **IDs stay in sync:** every step has an ID (`P{phase}-S{step}`, e.g. `P1-S2`) used identically in `CHECKLIST.md`.
- Goal: never lose the original structure and understanding; never let ad-hoc changes create chaos.

## 4. Status legend
- `[x]` done · `[~]` in progress · `[ ]` planned
- ⚠️ **NEEDS-SPEC** — defined but under-specified (we do not yet fully understand the end result). Carries a note on **what** to clarify and **when**. Must be resolved with the maintainer before that step starts.

## 5. Tooling & services (master list)

**Confirmed:**
- Dev env: Ubuntu 22.04 VPS, VSCode Remote-SSH. Agent: Claude Code (Claude for judgment; DeepSeek v4 for mechanical tasks).
- Frontend: React + Vite + TypeScript + KLineChart, pnpm.
- Backend: Python 3.12 + FastAPI + uvicorn, uv.
- Orchestration: Docker + docker-compose. VCS/CI: Git + GitHub + GitHub Actions.
- Security: gitleaks (pre-commit hook + CI job), GitHub native secret scanning + push protection. Config via pydantic-settings + `.env`/`.env.example`.
- Data: Binance (crypto, public API). FXCM/ForexConnect (forex — existing code to be wrapped).

**Planned / candidate (NOT finalized):**
- Data: Twelve Data, Finnhub (forex/stocks/metals). ⚠️ choose before `P1-S4`/`P5`.
- Backtesting: VectorBT (primary), Backtrader / Backtesting.py (secondary). ⚠️ integration boundary TBD (`P5`).
- Economic calendar provider. ⚠️ no clear free open API — research before `P6`.
- TradingView Advanced Charts (premium licensed layer). ⚠️ decide whether to apply (approval has lead time); revisit after `P2`/`P3`.
- Bots: Freqtrade / Jesse as reference. ⚠️ scope TBD (`P7`).
- Auth/accounts + database. ⚠️ required if layouts/journal are server-side; decide before `P4`/`P6`.
- Deployment: reverse proxy, domain, SSL on the VPS. ⚠️ before first public deploy.

## 6. Phases & steps

### P0 — Foundation
**Goal:** a repository with green CI and the agent loop working, *before* any feature code.
- `[x] P0-S1` — GitHub repository created (public, empty). Tools: GitHub. **Done.**
- `[x] P0-S2` — Project documentation established: `CLAUDE.md`, `ROADMAP.md`, `CHECKLIST.md`. **Done.**
- `[x] P0-S3` — Local repo init → connect remote → first commit & push (docs + `.gitignore` incl. `.env` + `.env.example` + `README.md`). Tools: git. **Done.**
- `[x] P0-S4` — Base tooling on VPS. **Done** (uv installed; git, Node 22 LTS + pnpm, Docker, Claude Code already present).
- `[x] P0-S5` — **Secret-leak prevention:** enable GitHub push protection (Settings → Advanced Security → Secret Protection); install gitleaks as a pre-commit hook (via the pre-commit framework); confirm `.env` is ignored and `.env.example` is present. Tools: gitleaks, pre-commit, GitHub Secret Protection.
- `[x] P0-S6` — Monorepo structure: `frontend/`, `backend/`, `shared/`.
- `[x] P0-S7` — Backend skeleton: FastAPI + uv, `/health` endpoint + test. Tools: FastAPI, uv, pytest.
- `[x] P0-S8` — Frontend skeleton: Vite + React + TS; install `klinecharts`. Tools: pnpm, Vite.
- `[x] P0-S9` — Local orchestration: `docker-compose` (backend + frontend). Tools: Docker.
- `[x] P0-S10` — CI gates: GitHub Actions (ruff/mypy/pytest + typecheck/test/build + **gitleaks secret scan**); protect `main`. Tools: GitHub Actions, gitleaks.
- `[x] P0-S11` — Wire Claude Code: run `/init`, merge into `CLAUDE.md`, confirm model routing; run one trial module through the agent → CI → review → merge loop. Tools: Claude Code.
- `[ ] P0-S10a` — Add `pnpm lint` (ESLint) as a frontend gate in CI. Detected during P0-S11 `/init` review: the script exists in `package.json` but is not enforced by CI. Tools: GitHub Actions, ESLint.

### P1 — Data layer & candle engine
**Goal:** a live, multi-source chart working end-to-end for ≥1 crypto and ≥1 forex symbol.
- `[x] P1-S1` — Define provider-neutral `DataSource` interface (history + live tick/bar contract) and shared `Tick`/`Candle` types; engine consumes a single `price` float (adapter derives mid/last-trade). Include an in-memory fake source for tests.
- `[x] P1-S2` — Port candle/timeframe engine from `server.py` into pure `backend/app/candles/` (per-symbol; no broker/network imports; preserve nuances). Source split (CHANGED): M1 ready from provider, M3/M5/M15 aggregated from M1, H1/H4/D1 loaded ready; sub-minute (S5–S30) live-only. Seamless history→live seam (seed last close per TF → first live open = that close for ≥M1). Tests MUST cover: open = prev close for ≥M1, open = price for sub-minute, first candle opens at price; M1→M3/M5/M15 aggregation; H1/H4/D1 accepted as ready bars; empty history for sub-minute; seamless seam; last in-progress bar dropped on load.
- `[ ] P1-S3` — FXCM adapter behind `DataSource` (FXCM = primary live forex source). **Design (resolved):** the official `forexconnect` Python binding is frozen at Python 3.5–3.7 (last release 2021) and will not install on the 3.12 backend, so ForexConnect runs as an isolated **feeder process** on Python 3.7 (the existing `server.py`, trimmed to data-only) exposing prices over a local channel; the in-process FXCM `DataSource` adapter (3.12) is a **client** to that feeder. Credentials via env (pydantic-settings); old hardcoded creds NOT ported. Orchestrated via docker-compose. Rationale: quarantines a dead-end dependency behind the swappable `DataSource` so it can be replaced later without touching engine/UI. **Runs after P1-S7** (build the full Binance pipeline S5→S6→S7 first).
- `[x] P1-S4` — Binance adapter (crypto, public REST + WebSocket). **Runs before P1-S3** — a modern 3.12-native source that validates the full source → engine → REST → frontend pipeline end-to-end first.
- `[ ] P1-S5` — REST endpoints: `/candles` (symbol, timeframe) + history loading. Serve FastAPI's auto-generated OpenAPI schema and export it so the frontend generates types from it (architecture rule #5) — no hand-written frontend types.
- `[ ] P1-S6` — WebSocket live streaming to the frontend.
- `[ ] P1-S7` — Frontend `ChartEngine` wrapper over KLineChart; render candles from backend; timeframe switching. Also enable `strict: true` in `frontend/tsconfig.app.json` (currently off; required by our TS-strict rule) before writing real frontend code.
- `[ ] P1-S4a` — Add `.dockerignore` (root + backend/frontend as needed) to keep `.env`, `.git`, `node_modules`, and caches out of the Docker build context. Deferred hygiene; non-blocking. Flagged in external review (2026-07).
- `[ ] P1-S4b` — Harden `BinanceDataSource`: auto-reconnect on WebSocket drop + basic rate-limit/backoff (the old `server.py` had a reconnect loop). Deferred hardening; non-blocking for dev. Flagged in external review (2026-07).

### P2 — Indicators & chart features
**Goal:** built-in indicators and core chart UX on top of the wrapper.
⚠️ **NEEDS-SPEC:** which indicators ship first; custom-indicator registration approach — clarify before P2. *(Steps detailed when P2 is reached.)*

### P3 — Drawing tools & custom indicators
⚠️ **NEEDS-SPEC:** evaluate community KLineChart forks (undo/redo, indicator editor) vs building on the official API — decide at the start of P3. *(Steps detailed when reached.)*

### P4 — Multi-window layouts & persistence
⚠️ **NEEDS-SPEC:** persistence model (local vs server-side) depends on the auth decision — clarify before P4. *(Steps detailed when reached.)*

### P5 — Backtesting
⚠️ **NEEDS-SPEC:** VectorBT integration boundary, result schema, run/report UI; and whether to port the old signal engines (`market_engine`, `structure_engine`, `signal_engine`, `pattern_memory`, `signal_tracker`) — clarify before P5. *(Steps detailed when reached.)*

### P6 — Economic calendar & trading journal
⚠️ **NEEDS-SPEC:** economic-calendar data provider (free open API unclear); journal data model & storage — clarify before P6. *(Steps detailed when reached.)*

### P7 — Bots / strategies
⚠️ **NEEDS-SPEC:** authoring model (visual builder vs code), live-execution scope, Freqtrade/Jesse integration — major design decision; clarify before P7. *(Steps detailed when reached.)*

## 7. Cross-cutting open decisions (architecturally early)
Not tied to one phase, but decide before the phase that needs them:
- **User accounts / auth + database** — before P4/P6 (gates server-side layouts and journal).
- **TradingView Advanced Charts premium layer** — license application has lead time; revisit after P2/P3 once KLineChart limits are understood.
- **Deployment topology on the VPS** — dev vs prod separation, reverse proxy, domain, SSL — before the first deploy.

## 8. Change log
Record every roadmap change here (date — what changed — why). Keeps the project's evolution traceable.
- (init) — Roadmap created at P0 (only the empty GitHub repo existed).
- (update) — Added **P0-S5 secret-leak prevention** and a gitleaks scan to the CI step; renumbered former P0-S5..S10 to S6..S11. Chosen local scanner: **gitleaks** (one tool for both pre-commit and CI). Strengthened the Secrets section in `CLAUDE.md` to a layered approach.
- (update) — Marked P0-S2..S4 done. Corrected environment to **Ubuntu 22.04** (was 24). Confirmed Docker and Claude Code already installed on the VPS.
- (update) — Standardized the Node version to **Node 22 LTS** across docs to match the frontend `Dockerfile` (`node:22-alpine`) and CI (`node-version: 22`); earlier notes said Node 24.
- (update) — Phase 0 closed. Marked P0-S11 done after running `/init` and the trial agent → CI → review → merge loop. Added new step **P0-S10a** to add `pnpm lint` to CI (deferred follow-up flagged by Claude Code during `/init`).
- (update) — Phase 1 kickoff specs pinned. P1-S1: provider-neutral interface + `Tick`/`Candle` types, engine takes one price float, in-memory fake source. P1-S2: per-symbol pure engine; **source split changed vs `server.py`** — H1 now loaded ready (was aggregated from M1), aggregation = M3/M5/M15 only, direct-load = H1/H4/D1; history→live seam made seamless (seed last close per TF, no gap at load boundary); full test list added. Security: FXCM creds hardcoded in old `server.py` treated as compromised — NOT ported; secrets via env (pydantic-settings), per P1-S3.
- (update) — P1-S1 done: provider-neutral `DataSource` contract (`Tick`/`Candle` models, `load_history` + `stream_ticks`, in-memory `FakeDataSource`, 7 tests). Implementation notes: renamed the models module to `models.py` (a file named `types.py` shadows the stdlib `types` module and breaks mypy); added `app/__init__.py` and `app/data/__init__.py` package markers (required once `app/` gained a sub-package).
- (update) — P1-S2 done: pure `CandleEngine` ported from `server.py` into `backend/app/candles/` (per-symbol; no broker/network imports). Live open rule preserved (prev close for ≥M1, price for sub-minute); M3/M5/M15 aggregated from M1; H1/H4/D1 loaded ready; seamless history→live seam added; in-progress bar dropped on load. 15 engine tests (22 total) green.
- (update) — P1-S3 NEEDS-SPEC resolved. FXCM confirmed as the primary live forex source. ForexConnect's Python binding is frozen at Python 3.5–3.7 (incompatible with the 3.12 backend), so the FXCM adapter = an isolated ForexConnect feeder process (Python 3.7, data-only, from the existing `server.py`) behind the swappable `DataSource`; the 3.12 adapter is a client to it. Execution order changed: Binance (P1-S4) now runs before FXCM (P1-S3) to get an end-to-end chart on a modern source first.
- (update) — P1-S4 done: `BinanceDataSource` behind `DataSource` (REST `/api/v3/klines` history + `@trade` WebSocket live ticks; price = trade price; ms→s timestamps; sub-minute → empty, live-only). Networking is injectable for network-free tests (6 tests, 28 total). Added httpx + websockets runtime deps. Live-verified on the VPS (1000 M1 candles + live BTC ticks).
- (update) — Phase 1 reordered: build the end-to-end pipeline on Binance first (P1-S5 → P1-S6 → P1-S7), then P1-S3 (FXCM feeder) last, so the full source→engine→REST→WS→chart chain is proven before adding the second process. Folded scope: OpenAPI export → P1-S5 (arch rule #5); `strict: true` (tsconfig.app.json) → P1-S7. Added deferred non-blocking items P1-S4a (`.dockerignore`) and P1-S4b (Binance reconnect/rate-limit), flagged in external review.
