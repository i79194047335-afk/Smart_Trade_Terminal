"""
API dependencies.

FastAPI "dependencies" are small functions that supply things an endpoint
needs. Here we supply the market-data source. Keeping it behind a dependency
means the endpoint never names a concrete provider directly: production uses
Binance, while tests swap in a fake source via ``app.dependency_overrides`` —
no network required.
"""

from app.data.base import DataSource
from app.data.binance import BinanceDataSource


def get_data_source() -> DataSource:
    """Return the market-data source the API should use.

    Currently Binance (the only implemented provider). When more providers
    exist this can choose one, but every caller still receives the neutral
    ``DataSource`` interface.
    """
    return BinanceDataSource()
