"""
Tests for the ``/candles`` REST endpoint (P1-S5).

No network is used: a ``FakeDataSource`` is injected via FastAPI's dependency
override, so the endpoint is tested end-to-end (HTTP request → engine → JSON)
deterministically. These verify the loading strategy per timeframe and the
response shape.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_data_source
from app.data.fake import FakeDataSource
from app.data.models import Candle
from app.main import app

SYMBOL = "BTCUSDT"


def m1_bar(i: int) -> Candle:
    """Build a distinct M1 bar at minute ``i``."""
    return Candle(
        time=i * 60,
        open=float(i),
        high=float(i) + 1,
        low=float(i) - 1,
        close=float(i) + 0.5,
    )


@pytest.fixture
def client_with_source() -> Iterator[tuple[TestClient, FakeDataSource]]:
    """Yield a test client whose data source is a controllable fake."""
    fake = FakeDataSource()
    app.dependency_overrides[get_data_source] = lambda: fake
    try:
        yield TestClient(app), fake
    finally:
        # Always clear the override so tests stay isolated.
        app.dependency_overrides.clear()


def test_m1_returns_closed_history(
    client_with_source: tuple[TestClient, FakeDataSource],
) -> None:
    """M1 request returns loaded M1 history minus the in-progress bar."""
    client, fake = client_with_source
    fake._history[(SYMBOL, "M1")] = [m1_bar(i) for i in range(4)]  # 4 bars

    response = client.get("/candles", params={"symbol": SYMBOL, "timeframe": "M1"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # last (in-progress) bar dropped
    assert data[0] == {"time": 0, "open": 0.0, "high": 1.0, "low": -1.0, "close": 0.5}


def test_m5_is_aggregated_from_m1(
    client_with_source: tuple[TestClient, FakeDataSource],
) -> None:
    """M5 request aggregates from M1 history."""
    client, fake = client_with_source
    fake._history[(SYMBOL, "M1")] = [m1_bar(i) for i in range(10)]  # minutes 0..9

    response = client.get("/candles", params={"symbol": SYMBOL, "timeframe": "M5"})

    assert response.status_code == 200
    data = response.json()
    # Only the [0,300) bucket survives (last aggregated bar dropped).
    assert data == [{"time": 0, "open": 0.0, "high": 5.0, "low": -1.0, "close": 4.5}]


def test_h1_uses_ready_history(
    client_with_source: tuple[TestClient, FakeDataSource],
) -> None:
    """H1 request returns ready bars loaded directly for that timeframe."""
    client, fake = client_with_source
    fake._history[(SYMBOL, "H1")] = [
        Candle(time=0, open=1.0, high=2.0, low=0.5, close=1.5),
        Candle(time=3600, open=1.5, high=2.5, low=1.0, close=2.0),
        Candle(time=7200, open=2.0, high=3.0, low=1.5, close=2.5),  # in-progress
    ]

    response = client.get("/candles", params={"symbol": SYMBOL, "timeframe": "H1"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # last bar dropped
    assert data[-1]["time"] == 3600


def test_subminute_returns_empty(
    client_with_source: tuple[TestClient, FakeDataSource],
) -> None:
    """Sub-minute timeframes have no history and return an empty list."""
    client, _ = client_with_source
    response = client.get("/candles", params={"symbol": SYMBOL, "timeframe": "S5"})
    assert response.status_code == 200
    assert response.json() == []


def test_unknown_timeframe_is_422(
    client_with_source: tuple[TestClient, FakeDataSource],
) -> None:
    """An unrecognised timeframe is rejected with 422."""
    client, _ = client_with_source
    response = client.get("/candles", params={"symbol": SYMBOL, "timeframe": "M2"})
    assert response.status_code == 422


def test_response_matches_candle_schema(
    client_with_source: tuple[TestClient, FakeDataSource],
) -> None:
    """Each returned item has exactly the CandleOut fields."""
    client, fake = client_with_source
    fake._history[(SYMBOL, "M1")] = [m1_bar(i) for i in range(3)]

    response = client.get("/candles", params={"symbol": SYMBOL, "timeframe": "M1"})

    assert response.status_code == 200
    for item in response.json():
        assert set(item.keys()) == {"time", "open", "high", "low", "close"}
