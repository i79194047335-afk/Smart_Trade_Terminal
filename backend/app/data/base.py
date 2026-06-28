"""
The ``DataSource`` contract.

This is the single interface every market-data provider must implement —
FXCM, Binance, Twelve Data, Finnhub, and any future source. The rest of the
application only ever talks to *this* interface, never to a specific provider.
That is what makes providers interchangeable: swap the implementation behind
the interface and nothing else has to change.

This file defines the contract only. It contains no networking and no
provider-specific code — those live in concrete adapters added in later steps.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.data.models import Candle, Tick


class DataSource(ABC):
    """Abstract base class describing what every data provider must offer.

    A ``DataSource`` exposes exactly two capabilities:

    1. Historical candles — a finite list of past bars, used to fill the chart
       when it first loads.
    2. A live tick stream — an open-ended feed of new prices as they arrive,
       used to keep the chart updating in real time.

    Concrete subclasses (the real adapters) provide the actual implementation.
    This class cannot be instantiated directly; that is enforced by ``ABC``
    together with the ``@abstractmethod`` markers below.
    """

    @abstractmethod
    async def load_history(self, symbol: str, timeframe: str) -> list[Candle]:
        """Return past candles for one symbol and timeframe.

        Args:
            symbol: Instrument identifier, e.g. ``"EUR/USD"``.
            timeframe: Timeframe label, e.g. ``"M1"``, ``"H1"``, ``"D1"``. The
                canonical set of timeframes is owned by the candle engine
                (P1-S2); at this contract boundary it is just an agreed string.

        Returns:
            Candles ordered oldest-first. May be empty — for example a
            provider/timeframe combination with no available history.
        """
        ...

    @abstractmethod
    def stream_ticks(self, symbol: str) -> AsyncIterator[Tick]:
        """Yield live ticks for one symbol as they arrive.

        This is an asynchronous stream: the caller consumes it with
        ``async for``, receiving each new ``Tick`` the moment the provider
        reports it. The stream is open-ended — it runs until the caller stops
        listening or the connection ends.

        Args:
            symbol: Instrument identifier to subscribe to.

        Returns:
            An async iterator of ``Tick`` objects.
        """
        ...
