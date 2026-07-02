"""
Request/response schemas for the HTTP API.

These Pydantic models define the exact JSON shapes the API accepts and returns.
FastAPI turns them into the OpenAPI schema automatically, which the frontend
uses to generate its own types (architecture rule #5) — so the shape is defined
once, here, and never hand-copied on the frontend.
"""

from pydantic import BaseModel


class CandleOut(BaseModel):
    """One OHLC candle as returned by the API.

    Mirrors the internal ``Candle`` model but is a separate, explicit API type
    so the wire format stays stable even if internals change.

    Attributes:
        time: Bar open time, Unix seconds (UTC).
        open: Price at the start of the bar.
        high: Highest price in the bar.
        low: Lowest price in the bar.
        close: Last price in the bar.
    """

    time: int
    open: float
    high: float
    low: float
    close: float
