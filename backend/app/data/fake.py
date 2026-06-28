"""
An in-memory fake data source for tests.

``FakeDataSource`` implements the ``DataSource`` contract without any network
or provider. You hand it canned history and a canned list of ticks up front,
and it plays them back. This lets us test the candle engine (P1-S2) and other
consumers deterministically — same input, same output, every run — with no
brokers and no internet involved.
"""

from collections.abc import AsyncIterator

from app.data.base import DataSource
from app.data.models import Candle, Tick


class FakeDataSource(DataSource):
    """A ``DataSource`` that simply replays pre-supplied data.

    Args:
        history: Canned candles keyed by ``(symbol, timeframe)``.
            ``load_history`` returns the matching list, or an empty list if the
            key is unknown. Defaults to empty.
        ticks: Canned ticks keyed by symbol. ``stream_ticks`` yields them in
            order. Defaults to empty.
    """

    def __init__(
        self,
        history: dict[tuple[str, str], list[Candle]] | None = None,
        ticks: dict[str, list[Tick]] | None = None,
    ) -> None:
        # Fall back to empty mappings so the object is always usable, even when
        # constructed with no arguments (handy in tests that only need one half).
        self._history = history or {}
        self._ticks = ticks or {}

    async def load_history(self, symbol: str, timeframe: str) -> list[Candle]:
        """Return the canned history for ``(symbol, timeframe)``, or empty.

        Returns a fresh list copy so callers cannot accidentally mutate the
        fake's internal data through the value they receive.
        """
        return list(self._history.get((symbol, timeframe), []))

    async def stream_ticks(self, symbol: str) -> AsyncIterator[Tick]:
        """Yield the canned ticks for ``symbol``, one by one, in order.

        Implemented as an async generator (note the ``yield``) — exactly how a
        real adapter will surface live prices in later steps.
        """
        for tick in self._ticks.get(symbol, []):
            yield tick
