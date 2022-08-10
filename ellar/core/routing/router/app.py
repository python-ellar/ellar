import typing as t
from functools import wraps
from types import FunctionType

from starlette.routing import BaseRoute, Router as StarletteRouter

from ellar.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
)
from ellar.reflect import reflect
from ellar.types import ASGIApp, TReceive, TScope, TSend

from .route_collections import RouteCollection

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver

__all__ = ["ApplicationRouter"]


def router_default_decorator(func: ASGIApp) -> ASGIApp:
    @wraps(func)
    async def _wrap(scope: TScope, receive: TReceive, send: TSend) -> None:
        version_scheme_resolver: "BaseAPIVersioningResolver" = t.cast(
            "BaseAPIVersioningResolver", scope[SCOPE_API_VERSIONING_RESOLVER]
        )
        if version_scheme_resolver and version_scheme_resolver.matched_any_route:
            version_scheme_resolver.raise_exception()

        await func(scope, receive, send)

    return _wrap


class ApplicationRouter(StarletteRouter):
    routes: RouteCollection  # type: ignore

    def __init__(
        self,
        routes: t.Sequence[BaseRoute],
        redirect_slashes: bool = True,
        default: ASGIApp = None,
        on_startup: t.Sequence[t.Callable] = None,
        on_shutdown: t.Sequence[t.Callable] = None,
        lifespan: t.Callable[[t.Any], t.AsyncContextManager] = None,
    ):
        super().__init__(
            routes=None,
            redirect_slashes=redirect_slashes,
            default=default,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
        )
        self.default = router_default_decorator(self.default)
        self.routes: RouteCollection = RouteCollection(routes)

    def append(self, item: t.Union[BaseRoute, t.Callable]) -> None:
        _item: t.Any = item
        if callable(_item) and type(_item) == FunctionType:
            _item = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, _item)
        self.routes.append(_item)

    def extend(self, routes: t.Sequence[t.Union[BaseRoute, t.Callable]]) -> None:
        for route in routes:
            self.append(route)

    def add_route(
        self,
        path: str,
        endpoint: t.Callable,
        methods: t.List[str] = None,
        name: str = None,
        include_in_schema: bool = True,
    ) -> None:  # pragma: no cover
        """Not supported"""

    def add_websocket_route(
        self, path: str, endpoint: t.Callable, name: str = None
    ) -> None:  # pragma: no cover
        """Not supported"""

    def route(
        self,
        path: str,
        methods: t.List[str] = None,
        name: str = None,
        include_in_schema: bool = True,
    ) -> t.Callable:  # pragma: no cover
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def websocket_route(
        self, path: str, name: str = None
    ) -> t.Callable:  # pragma: no cover
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def add_event_handler(
        self, event_type: str, func: t.Callable
    ) -> None:  # pragma: no cover
        """Not supported"""

    def on_event(self, event_type: str) -> t.Callable:  # pragma: no cover
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def mount(
        self, path: str, app: ASGIApp, name: str = None
    ) -> None:  # pragma: nocover
        """Not supported"""

    def host(
        self, host: str, app: ASGIApp, name: str = None
    ) -> None:  # pragma: no cover
        """Not supported"""
