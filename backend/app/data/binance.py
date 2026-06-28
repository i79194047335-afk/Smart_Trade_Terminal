"""
Binance market-data adapter.

Implements the ``DataSource`` contract for Binance crypto using Binance's free,
public market data — no API key required. History comes from the REST "klines"
endpoint; the live tick stream comes from the ``@trade`` WebSocket stream (each
trade becomes one ``Tick`` whose price is the trade price).

The networking is intentionally injectable: the constructor accepts a kline
fetcher and a trade-stream opener, which default to real httpx/websockets
implementations but can be replaced with fakes in tests. This keeps the
parsing/mapping logic fully testable without any network access.

Binance symbols are upper-case with no separator, e.g. ``"BTCUSDT"``. This
adapter upper-cases the symbol at its boundary, so the ``Tick``/``Candle`` it
produces always carry the canonical upper-case symbol.
"""

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import httpx
import websockets

from app.data.base import DataSource
from app.data.models import Candle, Tick

# Map our timeframe labels to Binance kline intervals. Sub-minute timeframes
# (S5..S30) are deliberately absent: Binance has no 5/10/15/30-second klines,
# and in our model sub-minute history does not exist (those are live-only).
_BINANCE_INTERVAL: dict[str, str] = {
    "M1": "1m",
    "M3": "3m",
    "M5": "5m",
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}

# Type aliases for the injectable networking functions.
# A kline fetcher takes (symbol, interval, limit) and returns Binance's raw
# kline rows (a list of lists). A trade-stream opener takes a symbol and yields
# raw trade messages (already-decoded dicts) as they arrive.
KlineFetcher = Callable[[str, str, int], Awaitable[list[list[Any]]]]
TradeStreamOpener = Callable[[str], AsyncIterator[dict[str, Any]]]


def _parse_klines(raw: list[list[Any]]) -> list[Candle]:
    """Convert Binance raw kline rows into our ``Candle`` objects.

    Each Binance row is ``[openTimeMs, open, high, low, close, ...]`` with the
    open time in milliseconds and the prices as strings. We keep only OHLC and
    convert the time to whole seconds (our standard).
    """
    candles: list[Candle] = []
    for row in raw:
        candles.append(
            Candle(
                time=int(row[0]) // 1000,  # ms -> s
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
            )
        )
    return candles


def _parse_trade(symbol: str, message: dict[str, Any]) -> Tick:
    """Convert one Binance ``@trade`` message into a ``Tick``.

    The relevant fields are ``p`` (trade price, a string) and ``T`` (trade time
    in milliseconds). The symbol is taken from the caller so the tick carries
    the exact symbol the consumer asked for.
    """
    return Tick(
        symbol=symbol,
        ts=int(message["T"]) // 1000,  # ms -> s
        price=float(message["p"]),
    )


class BinanceDataSource(DataSource):
    """A ``DataSource`` backed by Binance's public REST + WebSocket APIs.

    Unlike the candle engine, one instance can serve any number of symbols —
    the symbol is passed to each call.

    Args:
        rest_base: Base URL for the REST API.
        ws_base: Base URL for the raw WebSocket streams.
        history_limit: How many historical candles to request (Binance allows
            up to 1000 per call).
        fetch_klines: Optional override for the kline fetcher (used in tests).
        open_trade_stream: Optional override for the trade-stream opener
            (used in tests).
    """

    def __init__(
        self,
        *,
        rest_base: str = "https://api.binance.com",
        ws_base: str = "wss://stream.binance.com:9443/ws",
        history_limit: int = 1000,
        fetch_klines: KlineFetcher | None = None,
        open_trade_stream: TradeStreamOpener | None = None,
    ) -> None:
        self._rest_base = rest_base
        self._ws_base = ws_base
        self._history_limit = history_limit
        # Fall back to the real network implementations when no override given.
        self._fetch_klines = fetch_klines or self._default_fetch_klines
        self._open_trade_stream = open_trade_stream or self._default_open_trade_stream

    async def load_history(self, symbol: str, timeframe: str) -> list[Candle]:
        """Fetch historical candles for a symbol/timeframe from Binance.

        Sub-minute timeframes have no Binance equivalent and return an empty
        list, matching our "sub-minute is live-only" rule.
        """
        interval = _BINANCE_INTERVAL.get(timeframe)
        if interval is None:
            return []
        raw = await self._fetch_klines(symbol.upper(), interval, self._history_limit)
        return _parse_klines(raw)

    async def stream_ticks(self, symbol: str) -> AsyncIterator[Tick]:
        """Yield live ticks for a symbol from Binance's ``@trade`` stream."""
        sym = symbol.upper()
        async for message in self._open_trade_stream(sym):
            yield _parse_trade(sym, message)

    # ------------------------------------------------------- real network impls

    async def _default_fetch_klines(
        self, symbol: str, interval: str, limit: int
    ) -> list[list[Any]]:
        """Fetch raw klines over HTTP (the real implementation).

        Used unless a fake fetcher was injected. Hits ``GET /api/v3/klines``.
        """
        url = f"{self._rest_base}/api/v3/klines"
        params: dict[str, str | int] = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data: list[list[Any]] = response.json()
        return data

    async def _default_open_trade_stream(
        self, symbol: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Open the real ``@trade`` WebSocket and yield decoded messages.

        Used unless a fake stream was injected. The stream name must be the
        lower-cased symbol, e.g. ``btcusdt@trade``.
        """
        url = f"{self._ws_base}/{symbol.lower()}@trade"
        async with websockets.connect(url) as connection:
            async for raw in connection:
                message: dict[str, Any] = json.loads(raw)
                yield message
