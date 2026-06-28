"""
Tests for the pure candle engine (P1-S2).

These lock down the behaviours the roadmap requires us to preserve from the
original ``server.py``, plus the one intentional improvement (the seamless
history-to-live seam). Numbers are kept small so expected values can be checked
by hand.

Bar/tick helpers below keep each test readable: ``m1_bar`` builds one minute
bar, ``tick`` builds one price observation.
"""

from app.candles.engine import CandleEngine, aggregate
from app.data.models import Candle, Tick

SYMBOL = "EUR/USD"


def m1_bar(i: int) -> Candle:
    """Build a distinct M1 bar at minute ``i`` with easy-to-track OHLC."""
    return Candle(
        time=i * 60,
        open=float(i),
        high=float(i) + 1,
        low=float(i) - 1,
        close=float(i) + 0.5,
    )


def tick(ts: int, price: float) -> Tick:
    """Build a tick for the test symbol."""
    return Tick(symbol=SYMBOL, ts=ts, price=price)


# ---------------------------------------------------------------- live: open rule


def test_open_equals_prev_close_for_m1_and_above() -> None:
    """For M1+, a new candle opens at the previous candle's close (no gap)."""
    engine = CandleEngine(SYMBOL)
    engine.process_tick(tick(0, 1.0))  # first M1 candle opens at 1.0
    engine.process_tick(tick(10, 1.5))  # same M1 bucket -> close moves to 1.5
    engine.process_tick(tick(60, 1.2))  # next M1 bucket -> rolls over

    current = engine.current("M1")
    assert current is not None
    assert current.open == 1.5  # opened at the previous candle's close, not 1.2


def test_open_equals_price_for_subminute() -> None:
    """For sub-minute (S5), a new candle opens at the current price."""
    engine = CandleEngine(SYMBOL)
    engine.process_tick(tick(0, 1.0))  # first S5 candle opens at 1.0
    engine.process_tick(tick(2, 1.5))  # same S5 bucket [0,5) -> close 1.5
    engine.process_tick(tick(5, 1.2))  # next S5 bucket [5,10) -> rolls over

    current = engine.current("S5")
    assert current is not None
    assert current.open == 1.2  # sub-minute opens at price, not at prev close (1.5)


def test_first_candle_opens_at_price_without_history() -> None:
    """With no seeded history, the very first candle opens at the price."""
    engine = CandleEngine(SYMBOL)
    engine.process_tick(tick(0, 1.234))

    for timeframe in ("S5", "M1", "D1"):
        candle = engine.current(timeframe)
        assert candle is not None
        assert candle.open == 1.234


# --------------------------------------------------------------- history: aggregate


def test_m1_aggregation_to_m5() -> None:
    """M5 history is built from M1 by standard OHLC aggregation."""
    engine = CandleEngine(SYMBOL)
    engine.load_m1_history([m1_bar(i) for i in range(10)])  # minutes 0..9

    # Last M1 bar (minute 9) is dropped as in-progress -> minutes 0..8 retained.
    # M5 bucket [0,300) covers minutes 0..4; bucket [300,600) covers 5..8.
    # The last aggregated bar is also dropped, leaving only the [0,300) candle.
    m5 = engine.history("M5")
    assert m5 == [Candle(time=0, open=0.0, high=5.0, low=-1.0, close=4.5)]


def test_m1_aggregation_to_m3_count() -> None:
    """M3 aggregation produces the expected number of retained candles."""
    engine = CandleEngine(SYMBOL)
    engine.load_m1_history([m1_bar(i) for i in range(10)])  # minutes 0..9 -> 0..8 kept

    # M3 buckets over minutes 0..8: [0,3),[3,6),[6,9) = 3 candles; drop last -> 2.
    assert len(engine.history("M3")) == 2


def test_aggregate_function_directly() -> None:
    """The pure aggregate() helper merges bars within each bucket correctly."""
    bars = [m1_bar(i) for i in range(5)]  # minutes 0..4, all in one M5 bucket
    result = aggregate(bars, 300)
    assert result == [Candle(time=0, open=0.0, high=5.0, low=-1.0, close=4.5)]


# --------------------------------------------------------------- history: ready load


def test_ready_history_accepted_for_direct_timeframes() -> None:
    """H1/H4/D1 accept ready bars directly; last bar dropped as in-progress."""
    bars = [
        Candle(time=0, open=1.0, high=2.0, low=0.5, close=1.5),
        Candle(time=3600, open=1.5, high=2.5, low=1.0, close=2.0),
        Candle(time=7200, open=2.0, high=3.0, low=1.5, close=2.5),  # in-progress
    ]
    engine = CandleEngine(SYMBOL)
    engine.load_ready_history("H1", bars)
    assert engine.history("H1") == bars[:-1]


def test_ready_history_rejects_non_direct_timeframe() -> None:
    """Loading ready bars into an aggregated timeframe is an error."""
    engine = CandleEngine(SYMBOL)
    try:
        engine.load_ready_history("M5", [])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for non-direct timeframe")


def test_subminute_has_no_history() -> None:
    """Sub-minute timeframes never carry history."""
    engine = CandleEngine(SYMBOL)
    engine.load_m1_history([m1_bar(i) for i in range(10)])
    assert engine.history("S5") == []
    assert engine.history("S30") == []


def test_last_in_progress_bar_dropped_on_load() -> None:
    """The newest bar is dropped on load (it is the still-forming candle)."""
    engine = CandleEngine(SYMBOL)
    engine.load_m1_history([m1_bar(i) for i in range(4)])  # 4 bars -> 3 retained
    assert len(engine.history("M1")) == 3

    engine.load_ready_history(
        "D1",
        [
            Candle(time=0, open=1, high=2, low=0, close=1),
            Candle(time=86400, open=1, high=2, low=0, close=1),
            Candle(time=172800, open=1, high=2, low=0, close=1),
        ],
    )
    assert len(engine.history("D1")) == 2


# ------------------------------------------------------------------- seamless seam


def test_seamless_seam_m1_opens_at_last_seeded_close() -> None:
    """After history, the first live M1 candle opens at the last seeded close."""
    engine = CandleEngine(SYMBOL)
    engine.load_m1_history([m1_bar(0), m1_bar(1), m1_bar(2)])
    # Minute 2 dropped as in-progress; last retained close is bar 1's close (1.5).

    engine.process_tick(tick(300, 9.9))  # first live tick, much later, price 9.9
    m1 = engine.current("M1")
    assert m1 is not None
    assert m1.open == 1.5  # continuous from seeded close, not the live price


def test_seam_does_not_apply_to_subminute() -> None:
    """Sub-minute first candle still opens at price even after history load."""
    engine = CandleEngine(SYMBOL)
    engine.load_m1_history([m1_bar(0), m1_bar(1), m1_bar(2)])
    engine.process_tick(tick(300, 9.9))
    s5 = engine.current("S5")
    assert s5 is not None
    assert s5.open == 9.9  # sub-minute has no seam; opens at price


# ----------------------------------------------------------------------- misc API


def test_series_is_closed_plus_current() -> None:
    """series() returns closed candles followed by the forming one."""
    engine = CandleEngine(SYMBOL)
    engine.process_tick(tick(0, 1.0))  # opens M1 candle (bucket 0)
    engine.process_tick(tick(60, 2.0))  # rolls -> closes bucket 0, opens bucket 60

    series = engine.series("M1")
    assert len(series) == 2
    assert series[0] == engine.history("M1")[0]
    assert series[-1] == engine.current("M1")


def test_tick_symbol_must_match_engine() -> None:
    """A tick for a different symbol is rejected."""
    engine = CandleEngine(SYMBOL)
    try:
        engine.process_tick(Tick(symbol="GBP/USD", ts=0, price=1.0))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on symbol mismatch")


def test_unknown_timeframe_rejected() -> None:
    """Accessors reject timeframe labels the engine does not know."""
    engine = CandleEngine(SYMBOL)
    try:
        engine.history("M2")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for unknown timeframe")
