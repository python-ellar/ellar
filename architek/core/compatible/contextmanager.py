import sys

if sys.version_info >= (3, 7):
    from contextlib import asynccontextmanager as asynccontextmanager
else:
    from contextlib2 import (  # noqa
        AsyncExitStack as AsyncExitStack,
        asynccontextmanager as asynccontextmanager,
    )
