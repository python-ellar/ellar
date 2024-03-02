"""
PyMemcacheCacheBackend inspired by Django PyMemcacheCache
"""

import typing as t

try:
    from pymemcache import HashClient
    from pymemcache.serde import pickle_serde
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "To use `PyMemcacheCacheBackend`, you have to install 'pymemcache' package e.g. `pip install pymemcache`"
    ) from e
from .base import BasePylibMemcachedCache


class Client(HashClient):
    """pymemcache client.
    Customize pymemcache behavior as python-memcached (default backend)'s one.
    """

    def __init__(self, servers: t.List[str], *args: t.Any, **kwargs: t.Any) -> None:
        super(Client, self).__init__(
            self._split_host_and_port(servers), *args, **kwargs
        )

    def _split_host_and_port(self, servers: t.List[t.Any]) -> t.List[t.Tuple[str, int]]:
        """Convert python-memcached based server strings to pymemcache's one.
        - python-memcached: ['127.0.0.1:11211', ...] or ['127.0.0.1', ...]
        - pymemcache: [('127.0.0.1', 11211), ...]
        """
        _host_and_port_list = []
        for server in servers:
            connection_info = server.split(":")
            if len(connection_info) == 1:
                _host_and_port_list.append((connection_info[0], 11211))
            elif len(connection_info) == 2:
                _host_and_port_list.append(
                    (connection_info[0], int(connection_info[1]))
                )
        return _host_and_port_list

    def disconnect_all(self) -> None:
        for client in self.clients.values():
            client.close()


class PyMemcacheCacheBackend(BasePylibMemcachedCache):
    """An implementation of a cache binding using pymemcache."""

    MEMCACHE_CLIENT = Client

    def __init__(
        self, servers: t.List[str], options: t.Optional[t.Dict] = None, **kwargs: t.Any
    ):
        _default_options = options or {}

        _options = {
            "allow_unicode_keys": True,
            "default_noreply": False,
            "serde": pickle_serde,
            **_default_options,
        }

        super().__init__(servers, options=_options, **kwargs)

    def close(self, **kwargs: t.Any) -> None:
        self._cache_client.disconnect_all()
