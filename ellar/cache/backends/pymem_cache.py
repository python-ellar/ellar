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


class PyMemcacheCacheBackend(BasePylibMemcachedCache):
    """An implementation of a cache binding using pymemcache."""

    MEMCACHE_CLIENT = HashClient

    def __init__(self, servers: t.List[str], options: t.Dict = None, **kwargs: t.Any):

        _default_options = options or {}

        _options = {
            "allow_unicode_keys": True,
            "default_noreply": False,
            "serde": pickle_serde,
            **_default_options,
        }

        super().__init__(servers, options=_options, **kwargs)
