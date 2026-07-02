"""
The ``/candles`` REST endpoint.

Returns the history of *closed* candles for a symbol and timeframe. It wires
together the pieces already built: it loads history from a ``DataSource``
(Binance today), feeds it through the pure ``CandleEngine`` (which drops the
still-forming bar and aggregates M3/M5/M15 from M1), and returns the closed
candles for the requested timeframe.

The currently-forming candle is deliberately NOT returned here — that live,
updating bar is delivered over the WebSocket stream (P1-S6). This endpoint is
history only, which keeps it simple and cacheable.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_data_source
from app.api.schemas import CandleOut
from app.candles.engine import CandleEngine
from app.candles.timeframes import AGGREGATED_FROM_M1, READY_DIRECT, TF_SECONDS
from app.data.base import DataSource

router = APIRouter()


@router.get("/candles", response_model=list[CandleOut])
async def get_candles(
    symbol: str = Query(..., description="Instrument symbol, e.g. BTCUSDT"),
    timeframe: str = Query(..., description="Timeframe label, e.g. M1, M5, H1, D1"),
    source: DataSource = Depends(get_data_source),
) -> list[CandleOut]:
    """Return closed candles for ``symbol`` at ``timeframe``.

    Loading strategy mirrors the engine's source split:
    * H1/H4/D1 are loaded ready from the provider.
    * M1/M3/M5/M15 come from M1 history (M3/M5/M15 via aggregation).
    * Sub-minute timeframes have no history and return an empty list.

    Raises:
        HTTPException 422: if the timeframe label is not recognised.
    """
    if timeframe not in TF_SECONDS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown timeframe {timeframe!r}",
        )

    engine = CandleEngine(symbol)

    if timeframe in READY_DIRECT:
        # H1/H4/D1: fetch that timeframe directly and seed it as ready bars.
        bars = await source.load_history(symbol, timeframe)
        engine.load_ready_history(timeframe, bars)
    elif timeframe == "M1" or timeframe in AGGREGATED_FROM_M1:
        # M1 and the small aggregated frames are built from M1 history.
        m1_bars = await source.load_history(symbol, "M1")
        engine.load_m1_history(m1_bars)
    # Sub-minute (S5..S30): nothing to load — history stays empty.

    closed = engine.history(timeframe)
    # Convert internal candles to the explicit API type.
    return [
        CandleOut(
            time=candle.time,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
        )
        for candle in closed
    ]
