"""
Timeframe definitions for the candle engine.

A *timeframe* is the duration of one candle (e.g. M1 = one minute). This module
holds the single source of truth for which timeframes exist, how many seconds
each one spans, and how each one is sourced:

* ``M1`` — loaded ready from the provider; it is also the base used to build
  the small aggregated timeframes below.
* ``M3``/``M5``/``M15`` — built by aggregating M1 bars together.
* ``H1``/``H4``/``D1`` — loaded ready from the provider (a direct load gives
  enough history and the broker's correct session alignment; aggregating these
  from M1 would be both too short and misaligned).
* ``S5``/``S10``/``S15``/``S30`` (sub-minute) — built live from ticks only;
  they have no history.

Note: at runtime *every* timeframe's currently-forming candle is built live
from ticks. Aggregation is used only to seed the *historical* M3/M5/M15 bars.
"""

# Ordered map: timeframe label -> its length in seconds. Insertion order is
# preserved by Python dicts, so iterating this yields S5 .. D1 in order.
TF_SECONDS: dict[str, int] = {
    "S5": 5,
    "S10": 10,
    "S15": 15,
    "S30": 30,
    "M1": 60,
    "M3": 180,
    "M5": 300,
    "M15": 900,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}

# Timeframes whose history is produced by aggregating M1 bars.
AGGREGATED_FROM_M1: tuple[str, ...] = ("M3", "M5", "M15")

# Timeframes whose history is loaded ready (directly) from the provider.
# (M1 is the base load; H1/H4/D1 are loaded directly, not aggregated.)
READY_DIRECT: tuple[str, ...] = ("H1", "H4", "D1")

# Sub-minute timeframes: live-only, never have history.
SUBMINUTE: tuple[str, ...] = ("S5", "S10", "S15", "S30")


def is_subminute(timeframe: str) -> bool:
    """Return True if the timeframe is shorter than one minute (live-only)."""
    return TF_SECONDS[timeframe] < 60
