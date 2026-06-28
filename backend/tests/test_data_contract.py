"""
Contract tests for the data layer.

These verify two things about our agreed interface:

1. The basic data shapes (``Tick``, ``Candle``) behave as intended.
2. ``FakeDataSource`` honours the ``DataSource`` contract — returning canned
   history and replaying canned ticks.

Because every real adapter will implement the same contract, these tests also
document how consumers are expected to use *any* data source.

The data interface is asynchronous, so the async cases drive the coroutines
with ``asyncio.run`` — this keeps the test suite dependency-free (no extra
pytest plugin needed).
"""

import asyncio
from dataclasses import FrozenInstanceError

import pytest

from app.data.base import DataSource
from app.data.fake import FakeDataSource
from app.data.models import Candle, Tick


def test_tick_is_immutable() -> None:
    """A Tick's fields cannot be changed after creation (frozen dataclass)."""
    tick = Tick(symbol="EUR/USD", ts=1_700_000_000, price=1.2345)
    assert tick.symbol == "EUR/USD"
    assert tick.ts == 1_700_000_000
    assert tick.price == 1.2345
    with pytest.raises(FrozenInstanceError):
        tick.price = 9.9999  # type: ignore[misc]


def test_candle_holds_ohlc() -> None:
    """A Candle stores the five OHLC fields exactly as given."""
    candle = Candle(time=1_700_000_000, open=1.0, high=1.5, low=0.9, close=1.2)
    assert (candle.open, candle.high, candle.low, candle.close) == (1.0, 1.5, 0.9, 1.2)


def test_fake_is_a_datasource() -> None:
    """FakeDataSource really implements the DataSource interface."""
    assert isinstance(FakeDataSource(), DataSource)


def test_datasource_cannot_be_instantiated() -> None:
    """The abstract interface itself must not be usable directly."""
    with pytest.raises(TypeError):
        DataSource()  # type: ignore[abstract]


def test_load_history_returns_canned_candles() -> None:
    """load_history returns exactly the candles supplied for that key."""
    candle = Candle(time=60, open=1.0, high=1.1, low=0.9, close=1.05)
    source = FakeDataSource(history={("EUR/USD", "M1"): [candle]})
    result = asyncio.run(source.load_history("EUR/USD", "M1"))
    assert result == [candle]


def test_load_history_unknown_key_is_empty() -> None:
    """An unknown (symbol, timeframe) yields an empty list, not an error."""
    source = FakeDataSource()
    assert asyncio.run(source.load_history("BTCUSDT", "S5")) == []


def test_stream_ticks_replays_in_order() -> None:
    """stream_ticks yields the supplied ticks, in their original order."""
    ticks = [
        Tick(symbol="EUR/USD", ts=1, price=1.10),
        Tick(symbol="EUR/USD", ts=2, price=1.11),
    ]
    source = FakeDataSource(ticks={"EUR/USD": ticks})

    async def collect() -> list[Tick]:
        # ``async for`` consumes the live stream; here it just drains the fake.
        return [tick async for tick in source.stream_ticks("EUR/USD")]

    assert asyncio.run(collect()) == ticks
