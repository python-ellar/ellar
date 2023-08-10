"""
PyLibMCCacheBackend inspired by Django PyLibMCCache
"""
import typing as t

try:
    from pylibmc import Client
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "To use `PyLibMCCacheBackend`, you have to install 'pylibmc' package e.g. `pip install pylibmc`"
    ) from e

from .base import BasePylibMemcachedCache


class PyLibMCCacheBackend(BasePylibMemcachedCache):
    """An implementation of a cache binding using pylibmc"""

    MEMCACHE_CLIENT = Client

    def __init__(
        self, servers: t.List[str], options: t.Optional[t.Dict] = None, **kwargs: t.Any
    ):
        super().__init__(servers, options=options, **kwargs)

    async def close_async(self, **kwargs: t.Any) -> None:
        # libmemcached manages its own connections. Don't call disconnect_all()
        # as it resets the failover state and creates unnecessary reconnects.
        return None

    def close(self, **kwargs: t.Any) -> None:
        return None
