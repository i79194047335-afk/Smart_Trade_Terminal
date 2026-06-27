# Smart Trade Terminal — Checklist

> **Live progress tracker.** Mirrors the step IDs in `ROADMAP.md` exactly. Update after every completed step. Descriptions, goals, tools and clarification notes live in `ROADMAP.md` — this file is for tracking only.

## Legend
`[x]` done · `[~]` in progress · `[ ]` planned · ⚠️ blocked on a NEEDS-SPEC item (see `ROADMAP.md`)

## Current state
- **GitHub repo:** created; project docs pushed.
- **VPS tooling:** ready — git, Python, Node 24 + pnpm, uv, Docker, Claude Code.
- **Next action:** **P0-S10** — CI gates (GitHub Actions: ruff/mypy/pytest + typecheck/test/build + gitleaks).

## P0 — Foundation
- [x] P0-S1 — GitHub repo created (empty, public)
- [x] P0-S2 — Project docs authored (CLAUDE.md, ROADMAP.md, CHECKLIST.md)
- [x] P0-S3 — Local repo init + remote + first commit & push (docs, .gitignore, .env.example, README)
- [x] P0-S4 — Base tooling on VPS (Node 24 + pnpm, uv; Docker & Claude Code already present)
- [x] P0-S5 — Secret-leak prevention (enable GitHub push protection; gitleaks pre-commit hook; .env.example)
- [x] P0-S6 — Monorepo structure (frontend/, backend/, shared/)
- [x] P0-S7 — Backend skeleton (FastAPI + /health + test)
- [x] P0-S8 — Frontend skeleton (Vite + React + TS + klinecharts)
- [x] P0-S9 — docker-compose (local dev)
- [ ] P0-S10 — CI gates + gitleaks scan + branch protection on main
- [ ] P0-S11 — Claude Code wired + one trial module through the loop

## P1 — Data layer & candle engine
- [ ] P1-S1 — DataSource interface
- [ ] P1-S2 — Port candle/timeframe engine (+ tests for the nuances)
- [ ] P1-S3 — FXCM/ForexConnect adapter ⚠️ (clarify ForexConnect viability / role first)
- [ ] P1-S4 — Binance adapter
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
