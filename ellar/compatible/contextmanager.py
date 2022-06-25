import sys

if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager as asynccontextmanager  # noqa
else:
    from contextlib2 import asynccontextmanager as asynccontextmanager  # noqa
