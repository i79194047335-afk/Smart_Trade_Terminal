"""
The pure candle/timeframe engine.

Ported from the original ``server.py`` and kept deliberately pure: it takes
ticks and bars as input and produces OHLC candles per timeframe. It imports no
broker, no network, and no websocket code — only the shared ``Tick``/``Candle``
models. One engine instance handles exactly one symbol.

Two behaviours are carried over from the original code and must be preserved
(they are locked down by tests):

* **Continuous candles for M1 and above.** When a new candle opens, its
  ``open`` equals the previous candle's ``close`` — no gaps between bars.
* **Sub-minute candles open at price.** For S5..S30 the new candle's ``open``
  equals the current price instead.

One behaviour is an intentional improvement over the original:

* **Seamless history-to-live seam.** After seeding history, the engine
  remembers each timeframe's last close, so the first live candle (for M1 and
  above) opens at that close. The original opened the first live candle at the
  current price, leaving a visible gap at every page reload / reconnect.
"""

from app.candles.timeframes import (
    AGGREGATED_FROM_M1,
    READY_DIRECT,
    TF_SECONDS,
)
from app.data.models import Candle, Tick


def aggregate(bars: list[Candle], seconds: int) -> list[Candle]:
    """Merge finer bars into coarser candles of ``seconds`` length.

    Standard OHLC aggregation: within each time bucket the result takes the
    first bar's ``open``, the highest ``high``, the lowest ``low``, and the
    last bar's ``close``. Used to build historical M3/M5/M15 candles from M1.

    Args:
        bars: Source candles, oldest-first (typically M1 history).
        seconds: Target timeframe length in seconds.

    Returns:
        Aggregated candles, oldest-first.
    """
    result: list[Candle] = []
    bucket: int | None = None
    current: Candle | None = None

    for bar in bars:
        # Floor the bar's time down to the start of its target bucket.
        bar_bucket = (bar.time // seconds) * seconds
        if bar_bucket != bucket:
            # Entered a new bucket: finish the previous candle, start a fresh one.
            if current is not None:
                result.append(current)
            bucket = bar_bucket
            current = Candle(
                time=bar_bucket,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
            )
        else:
            # Same bucket: extend high/low and move close to this bar's close.
            current = Candle(
                time=current.time,  # type: ignore[union-attr]
                open=current.open,  # type: ignore[union-attr]
                high=max(current.high, bar.high),  # type: ignore[union-attr]
                low=min(current.low, bar.low),  # type: ignore[union-attr]
                close=bar.close,
            )

    if current is not None:
        result.append(current)
    return result


class CandleEngine:
    """Builds and holds candles for one symbol across all timeframes.

    The engine keeps, per timeframe: the list of closed candles, the single
    currently-forming candle, and the last known close (used to open the next
    candle seamlessly). Feed it history first (optional), then ticks.
    """

    def __init__(self, symbol: str) -> None:
        """Create an empty engine for one symbol.

        Args:
            symbol: The instrument this engine handles, e.g. ``"EUR/USD"``.
                Ticks for any other symbol are rejected.
        """
        self.symbol = symbol
        # Closed (finished) candles per timeframe, oldest-first.
        self._closed: dict[str, list[Candle]] = {tf: [] for tf in TF_SECONDS}
        # The single candle currently being built per timeframe (or None).
        self._current: dict[str, Candle | None] = {tf: None for tf in TF_SECONDS}
        # The time bucket the current candle belongs to, per timeframe.
        self._bucket: dict[str, int | None] = {tf: None for tf in TF_SECONDS}
        # Last known close per timeframe, used to open the next candle without
        # a gap. Seeded from history; updated as candles close.
        self._seed_close: dict[str, float | None] = {tf: None for tf in TF_SECONDS}

    # ----------------------------------------------------------------- history

    def load_m1_history(self, bars: list[Candle]) -> None:
        """Seed M1 history and build M3/M5/M15 from it.

        The newest bar is dropped because it is the still-forming (unclosed)
        candle — the live tick stream will rebuild the current bar itself.

        Args:
            bars: M1 candles from the provider (any order; sorted internally).
        """
        ordered = sorted(bars, key=lambda c: c.time)
        # Drop the last (in-progress) bar, mirroring the original server.py.
        m1_closed = ordered[:-1] if ordered else []
        self._closed["M1"] = list(m1_closed)
        self._seed_close["M1"] = m1_closed[-1].close if m1_closed else None

        # Build each aggregated timeframe from the (already-trimmed) M1 bars.
        for tf in AGGREGATED_FROM_M1:
            seconds = TF_SECONDS[tf]
            agg = aggregate(m1_closed, seconds)
            # The original drops the last aggregated bar too (it is in-progress).
            agg_closed = agg[:-1] if agg else []
            self._closed[tf] = agg_closed
            self._seed_close[tf] = agg_closed[-1].close if agg_closed else None

    def load_ready_history(self, timeframe: str, bars: list[Candle]) -> None:
        """Seed a directly-loaded timeframe (H1/H4/D1) with ready candles.

        Like M1 loading, the newest bar is dropped as the in-progress candle.

        Args:
            timeframe: One of H1/H4/D1.
            bars: Ready candles from the provider for that timeframe.

        Raises:
            ValueError: If ``timeframe`` is not a direct-load timeframe.
        """
        if timeframe not in READY_DIRECT:
            raise ValueError(
                f"{timeframe!r} is not a direct-load timeframe; "
                f"expected one of {READY_DIRECT}"
            )
        ordered = sorted(bars, key=lambda c: c.time)
        closed = ordered[:-1] if ordered else []
        self._closed[timeframe] = list(closed)
        self._seed_close[timeframe] = closed[-1].close if closed else None

    # -------------------------------------------------------------------- live

    def process_tick(self, tick: Tick) -> None:
        """Update every timeframe's current candle from one tick.

        For each timeframe this either starts a new candle (on the first tick
        or when the time bucket rolls over) or extends the current one.

        Args:
            tick: A single price observation for this engine's symbol.

        Raises:
            ValueError: If the tick's symbol does not match this engine.
        """
        if tick.symbol != self.symbol:
            raise ValueError(
                f"tick symbol {tick.symbol!r} does not match engine "
                f"symbol {self.symbol!r}"
            )

        price = tick.price
        for tf, seconds in TF_SECONDS.items():
            bucket = (tick.ts // seconds) * seconds
            current = self._current[tf]

            if current is None:
                # First candle for this timeframe. For M1+ open at the seeded
                # close if we have one (seamless seam); otherwise at price.
                self._open_new_candle(tf, seconds, bucket, price, is_first=True)
                continue

            if bucket != self._bucket[tf]:
                # Time bucket rolled over: close the current candle and open
                # the next. M1+ opens at the just-closed candle's close; sub-
                # minute opens at the current price.
                self._closed[tf].append(current)
                self._seed_close[tf] = current.close
                self._open_new_candle(tf, seconds, bucket, price, is_first=False)
                continue

            # Same bucket: extend the current candle with the new price.
            self._current[tf] = Candle(
                time=current.time,
                open=current.open,
                high=max(current.high, price),
                low=min(current.low, price),
                close=price,
            )

    def _open_new_candle(
        self,
        timeframe: str,
        seconds: int,
        bucket: int,
        price: float,
        *,
        is_first: bool,
    ) -> None:
        """Start a fresh current candle for one timeframe.

        Decides the ``open`` price by the rules above and stores the new candle
        and its bucket.

        Args:
            timeframe: The timeframe to open a candle for.
            seconds: That timeframe's length in seconds.
            bucket: The time bucket (start time) of the new candle.
            price: The current price.
            is_first: True if this is the very first candle for the timeframe
                (no candle has closed yet in this run).
        """
        seed_close = self._seed_close[timeframe]
        if seconds >= 60 and seed_close is not None:
            # M1 and above: continuous — open where the previous candle closed.
            open_price = seed_close
        else:
            # Sub-minute, or first candle with no seed: open at the price.
            open_price = price

        self._current[timeframe] = Candle(
            time=bucket,
            open=open_price,
            high=max(open_price, price),
            low=min(open_price, price),
            close=price,
        )
        self._bucket[timeframe] = bucket
        # ``is_first`` is accepted for clarity at the call sites; the open-price
        # rule above already covers both the first-candle and roll-over cases.
        _ = is_first

    # --------------------------------------------------------------- accessors

    def history(self, timeframe: str) -> list[Candle]:
        """Return the closed candles for a timeframe, oldest-first.

        Sub-minute timeframes have no history and return an empty list.
        """
        self._check_timeframe(timeframe)
        return list(self._closed[timeframe])

    def current(self, timeframe: str) -> Candle | None:
        """Return the currently-forming candle for a timeframe, or None."""
        self._check_timeframe(timeframe)
        return self._current[timeframe]

    def series(self, timeframe: str) -> list[Candle]:
        """Return closed candles plus the current one (if any), oldest-first.

        This is the full view a chart would draw for the timeframe.
        """
        self._check_timeframe(timeframe)
        closed = list(self._closed[timeframe])
        current = self._current[timeframe]
        if current is not None:
            closed.append(current)
        return closed

    @staticmethod
    def _check_timeframe(timeframe: str) -> None:
        """Raise if the timeframe label is not one we know about."""
        if timeframe not in TF_SECONDS:
            raise ValueError(
                f"unknown timeframe {timeframe!r}; expected one of {tuple(TF_SECONDS)}"
            )
