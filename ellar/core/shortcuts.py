import typing as t

from ellar.common.types import ASGIApp
from starlette.routing import Host, Mount


def mount(
    path: str, app: ASGIApp, name: t.Optional[str] = None
) -> Mount:  # pragma: no cover
    return Mount(path, app=app, name=name)


def host(
    host_: str, app: ASGIApp, name: t.Optional[str] = None
) -> Host:  # pragma: no cover
    return Host(host_, app=app, name=name)
