"""
Shared data models for the data layer.

These are the two basic shapes every part of the data layer agrees on:
a ``Tick`` (one price observation at a moment in time) and a ``Candle``
(an OHLC bar for a given timeframe). They are deliberately tiny and
provider-neutral: nothing here knows about FXCM, Binance, or any network.
Both the data-source adapters (which produce them) and the candle engine
(which consumes them) speak in terms of these types.
"""

from dataclasses import dataclass


# ``frozen=True`` makes instances immutable: once created, their fields cannot
# be changed by accident. That keeps market data trustworthy as it flows
# through the system. ``slots=True`` is a small memory/speed optimisation that
# also forbids adding unexpected attributes — a safety net against typos.
@dataclass(frozen=True, slots=True)
class Tick:
    """A single price observation for one symbol at one instant.

    Attributes:
        symbol: Instrument identifier, e.g. ``"EUR/USD"`` or ``"BTCUSDT"``.
        ts: Unix timestamp in whole seconds, UTC. Matches the time format used
            by the original ``server.py`` so old and new code stay aligned.
        price: The single price used to build candles. How it is derived is the
            adapter's job (forex: mid = (bid + ask) / 2; crypto: last trade
            price). The candle engine only ever sees this one number and never
            needs to know where it came from.
    """

    symbol: str
    ts: int
    price: float


@dataclass(frozen=True, slots=True)
class Candle:
    """An OHLC bar for one symbol and one timeframe.

    Attributes:
        time: Unix timestamp in whole seconds (UTC) of the bar's opening edge —
            the start of the time bucket this candle covers.
        open: Price at the start of the bar.
        high: Highest price seen during the bar.
        low: Lowest price seen during the bar.
        close: Most recent price in the bar (the final price once it closes).
    """

    time: int
    open: float
    high: float
    low: float
    close: float
