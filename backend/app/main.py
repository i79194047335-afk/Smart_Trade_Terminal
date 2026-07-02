"""
FastAPI application entry point.

Defines the HTTP API the frontend talks to. For now it only exposes a
/health endpoint used to verify the server is running. Real endpoints
(candles, websocket stream, ...) will be added in phase 1.
"""

from fastapi import FastAPI

from app.api.candles import router as candles_router

# `app` is the application object. FastAPI looks at the decorators below
# to know which URL maps to which Python function.
app = FastAPI(title="Smart Trade Terminal API")
# Mount the candles REST endpoints (history of closed candles).
app.include_router(candles_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Lightweight liveness probe.

    Returns a tiny JSON payload so external tools (and our CI) can confirm
    the API process is up. Intentionally returns a constant — no DB, no
    external calls — so it never fails for reasons unrelated to the server.
    """
    return {"status": "ok"}
