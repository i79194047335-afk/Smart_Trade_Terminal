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
- `[x] P0-S4` — Base tooling on VPS. **Done** (uv installed; git, Node 24 LTS + pnpm, Docker, Claude Code already present).
- `[x] P0-S5` — **Secret-leak prevention:** enable GitHub push protection (Settings → Advanced Security → Secret Protection); install gitleaks as a pre-commit hook (via the pre-commit framework); confirm `.env` is ignored and `.env.example` is present. Tools: gitleaks, pre-commit, GitHub Secret Protection.
- `[x] P0-S6` — Monorepo structure: `frontend/`, `backend/`, `shared/`.
- `[x] P0-S7` — Backend skeleton: FastAPI + uv, `/health` endpoint + test. Tools: FastAPI, uv, pytest.
- `[x] P0-S8` — Frontend skeleton: Vite + React + TS; install `klinecharts`. Tools: pnpm, Vite.
- `[ ] P0-S9` — Local orchestration: `docker-compose` (backend + frontend). Tools: Docker.
- `[ ] P0-S10` — CI gates: GitHub Actions (ruff/mypy/pytest + typecheck/test/build + **gitleaks secret scan**); protect `main`. Tools: GitHub Actions, gitleaks.
- `[ ] P0-S11` — Wire Claude Code: run `/init`, merge into `CLAUDE.md`, confirm model routing; run one trial module through the agent → CI → review → merge loop. Tools: Claude Code.

### P1 — Data layer & candle engine
**Goal:** a live, multi-source chart working end-to-end for ≥1 crypto and ≥1 forex symbol.
- `[ ] P1-S1` — Define `DataSource` interface (history + live tick/bar contract).
- `[ ] P1-S2` — Port candle/timeframe engine from `server.py` into pure `backend/app/candles/` (preserve nuances). Tests MUST cover: open = prev close for ≥M1, open = price for sub-minute; M1 → higher-TF aggregation; direct H4/D1 load behavior.
- `[ ] P1-S3` — FXCM/ForexConnect adapter behind `DataSource`; credentials via env (pydantic-settings). ⚠️ **NEEDS-SPEC:** confirm ForexConnect long-term viability; decide FXCM as a live source vs research-only — clarify before this step.
- `[ ] P1-S4` — Binance adapter (crypto, public REST + WebSocket).
- `[ ] P1-S5` — REST endpoints: `/candles` (symbol, timeframe) + history loading.
- `[ ] P1-S6` — WebSocket live streaming to the frontend.
- `[ ] P1-S7` — Frontend `ChartEngine` wrapper over KLineChart; render candles from backend; timeframe switching.

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
- (update) — Marked P0-S2..S4 done. Corrected environment to **Ubuntu 22.04** (was 24). Confirmed Node 24 LTS, Docker and Claude Code already installed on the VPS.
