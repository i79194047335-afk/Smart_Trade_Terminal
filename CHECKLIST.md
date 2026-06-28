# Smart Trade Terminal — Checklist

> **Live progress tracker.** Mirrors the step IDs in `ROADMAP.md` exactly. Update after every completed step. Descriptions, goals, tools and clarification notes live in `ROADMAP.md` — this file is for tracking only.

## Legend
`[x]` done · `[~]` in progress · `[ ]` planned · ⚠️ blocked on a NEEDS-SPEC item (see `ROADMAP.md`)

- **Phase 1 in progress.** Data contract + candle engine done.
- **P1-S2 done** — pure `CandleEngine` ported (per-symbol; aggregate M3/M5/M15; H1/H4/D1 ready; seamless seam); 22 tests green.
- **P1-S4 done** — `BinanceDataSource` behind `DataSource` (REST klines history + `@trade` WS stream); injectable networking; 6 tests (28 total) green; live-verified on VPS (1000 M1 candles + live BTC ticks).
- **Next:** P1-S3 — FXCM adapter via isolated ForexConnect feeder (Py3.7) + 3.12 client behind DataSource.

## P0 — Foundation
- [x] P0-S1 — GitHub repo created (empty, public)
- [x] P0-S2 — Project docs authored (CLAUDE.md, ROADMAP.md, CHECKLIST.md)
- [x] P0-S3 — Local repo init + remote + first commit & push (docs, .gitignore, .env.example, README)
- [x] P0-S4 — Base tooling on VPS (Node 22 + pnpm, uv; Docker & Claude Code already present)
- [x] P0-S5 — Secret-leak prevention (enable GitHub push protection; gitleaks pre-commit hook; .env.example)
- [x] P0-S6 — Monorepo structure (frontend/, backend/, shared/)
- [x] P0-S7 — Backend skeleton (FastAPI + /health + test)
- [x] P0-S8 — Frontend skeleton (Vite + React + TS + klinecharts)
- [x] P0-S9 — docker-compose (local dev)
- [x] P0-S10 — CI gates + gitleaks scan + branch protection on main
- [x] P0-S11 — Claude Code wired + one trial module through the loop
- [ ] P0-S10a — Add frontend ESLint gate to CI (`pnpm lint`)

## P1 — Data layer & candle engine
- [x] P1-S1 — DataSource interface + Tick/Candle types (provider-neutral; fake source)
- [x] P1-S2 — Port pure candle engine (per-symbol; source split H1→ready; seamless seam; nuance tests)
- [ ] P1-S3 — FXCM adapter = isolated ForexConnect feeder (Py3.7, from server.py) + 3.12 client behind DataSource (runs after P1-S4)
- [x] P1-S4 — Binance adapter (crypto, public REST + WebSocket) — runs first
- [ ] P1-S5 — REST /candles + history
- [ ] P1-S6 — WebSocket live stream
- [ ] P1-S7 — Frontend ChartEngine wrapper + timeframe switching

## P2 — Indicators & chart features ⚠️
- [ ] P2 — clarify indicator set + custom-indicator approach before start (steps detailed when reached)

## P3 — Drawing tools & custom indicators ⚠️
- [ ] P3 — decide community forks vs official API (steps detailed when reached)

## P4 — Multi-window layouts & persistence ⚠️
- [ ] P4 — depends on auth decision (steps detailed when reached)

## P5 — Backtesting ⚠️
- [ ] P5 — VectorBT boundary, result schema, port old engines? (steps detailed when reached)

## P6 — Economic calendar & trading journal ⚠️
- [ ] P6 — calendar provider, journal data model (steps detailed when reached)

## P7 — Bots / strategies ⚠️
- [ ] P7 — authoring model, execution scope (steps detailed when reached)

## Cross-cutting decisions (see ROADMAP §7)
- [ ] Auth / accounts + database — before P4/P6
- [ ] TradingView Advanced Charts premium layer — after P2/P3
- [ ] Deployment topology (dev/prod, reverse proxy, SSL) — before first deploy
