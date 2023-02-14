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

    def __init__(self, server: t.List[str], options: t.Dict = None, **kwargs: t.Any):
        super().__init__(server, library_client_type=Client, options=options, **kwargs)

    @property
    def client_servers(self) -> t.List[str]:
        output = []
        for server in self._servers:
            output.append(server.replace("unix:", ""))
        return output

    async def close_async(self, **kwargs: t.Any) -> None:
        # libmemcached manages its own connections. Don't call disconnect_all()
        # as it resets the failover state and creates unnecessary reconnects.
        return None

    def close(self, **kwargs: t.Any) -> None:
        return None
