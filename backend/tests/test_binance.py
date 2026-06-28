"""
Tests for the Binance data source (P1-S4).

No network is used: a fake kline fetcher and a fake trade stream are injected,
so the tests are deterministic and run anywhere. They cover the parsing/mapping
logic (the part most likely to be wrong) and the adapter's behaviour for
sub-minute timeframes.

The real network paths (``_default_fetch_klines`` / ``_default_open_trade_stream``)
are exercised live against Binance on the VPS, which has internet access.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from app.data.base import DataSource
from app.data.binance import (
    BinanceDataSource,
    _parse_klines,
    _parse_trade,
)
from app.data.models import Candle, Tick

# One real-shaped Binance kline row: [openTimeMs, open, high, low, close, ...].
SAMPLE_KLINE: list[Any] = [
    1_499_040_000_000,
    "0.01634790",
    "0.80000000",
    "0.01575800",
    "0.01577100",
    "148976.11427815",
    1_499_040_059_999,
]

# One real-shaped Binance @trade message (only the fields we use matter).
SAMPLE_TRADE: dict[str, Any] = {
    "e": "trade",
    "s": "BTCUSDT",
    "p": "25000.50",
    "q": "0.1",
    "T": 1_499_040_000_500,
}


def test_is_a_datasource() -> None:
    """BinanceDataSource implements the DataSource interface."""
    assert isinstance(BinanceDataSource(), DataSource)


def test_parse_klines_maps_fields() -> None:
    """Raw kline rows map to Candles with ms->s time and float prices."""
    result = _parse_klines([SAMPLE_KLINE])
    assert result == [
        Candle(
            time=1_499_040_000,  # ms / 1000
            open=0.01634790,
            high=0.80000000,
            low=0.01575800,
            close=0.01577100,
        )
    ]


def test_parse_trade_maps_price_and_time() -> None:
    """A trade message maps to a Tick with the trade price and ms->s time."""
    tick = _parse_trade("BTCUSDT", SAMPLE_TRADE)
    assert tick == Tick(symbol="BTCUSDT", ts=1_499_040_000, price=25000.50)


def test_load_history_uses_correct_interval() -> None:
    """load_history maps our TF label to the right Binance interval."""
    seen: dict[str, Any] = {}

    async def fake_fetch(symbol: str, interval: str, limit: int) -> list[list[Any]]:
        seen["symbol"] = symbol
        seen["interval"] = interval
        seen["limit"] = limit
        return [SAMPLE_KLINE]

    source = BinanceDataSource(fetch_klines=fake_fetch)
    result = asyncio.run(source.load_history("btcusdt", "H4"))

    assert seen["symbol"] == "BTCUSDT"  # upper-cased at the boundary
    assert seen["interval"] == "4h"  # H4 -> 4h
    assert result == _parse_klines([SAMPLE_KLINE])


def test_load_history_subminute_returns_empty_without_fetch() -> None:
    """Sub-minute timeframes return empty and never hit the network."""
    called = False

    async def fake_fetch(symbol: str, interval: str, limit: int) -> list[list[Any]]:
        nonlocal called
        called = True
        return []

    source = BinanceDataSource(fetch_klines=fake_fetch)
    assert asyncio.run(source.load_history("BTCUSDT", "S5")) == []
    assert called is False


def test_stream_ticks_parses_each_message() -> None:
    """stream_ticks yields a Tick per trade message, in order."""

    async def fake_stream(symbol: str) -> AsyncIterator[dict[str, Any]]:
        # The adapter should pass the upper-cased symbol to the opener.
        assert symbol == "BTCUSDT"
        for price, ts_ms in (("100.0", 1_000), ("101.0", 2_000)):
            yield {"p": price, "T": ts_ms}

    source = BinanceDataSource(open_trade_stream=fake_stream)

    async def collect() -> list[Tick]:
        return [tick async for tick in source.stream_ticks("btcusdt")]

    ticks = asyncio.run(collect())
    assert ticks == [
        Tick(symbol="BTCUSDT", ts=1, price=100.0),
        Tick(symbol="BTCUSDT", ts=2, price=101.0),
    ]
