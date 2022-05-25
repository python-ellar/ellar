import typing as t
from functools import wraps

from starlette.routing import (
    BaseRoute,
    Host as StarletteHost,
    Mount as StarletteMount,
    Router as StarletteRouter,
)

from ellar.compatible import DataMapper
from ellar.constants import SCOPE_API_VERSIONING_RESOLVER
from ellar.types import ASGIApp, TReceive, TScope, TSend

from ..operation_definitions import OperationDefinitions
from .route_collections import RouteCollection

if t.TYPE_CHECKING:
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
    operation_definition_class: t.Type[OperationDefinitions] = OperationDefinitions

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
        self._meta: t.Mapping = DataMapper()
        _route_definitions = self.operation_definition_class(t.cast(list, self.routes))

        self.Get = _route_definitions.get
        self.Post = _route_definitions.post

        self.Delete = _route_definitions.delete
        self.Patch = _route_definitions.patch

        self.Put = _route_definitions.put
        self.Options = _route_definitions.options

        self.Trace = _route_definitions.trace
        self.Head = _route_definitions.head

        self.HttpRoute = _route_definitions.http_route
        self.WsRoute = _route_definitions.ws_route

    def mount(self, path: str, app: ASGIApp, name: str = None) -> None:
        route = StarletteMount(path, app=app, name=name)
        self.routes.append(route)

    def host(self, host: str, app: ASGIApp, name: str = None) -> None:
        route = StarletteHost(host, app=app, name=name)
        self.routes.append(route)

    def add_route(
        self,
        path: str,
        endpoint: t.Callable,
        methods: t.List[str] = None,
        name: str = None,
        include_in_schema: bool = True,
    ) -> None:
        """Not supported"""

    def add_websocket_route(
        self, path: str, endpoint: t.Callable, name: str = None
    ) -> None:
        """Not supported"""

    def route(
        self,
        path: str,
        methods: t.List[str] = None,
        name: str = None,
        include_in_schema: bool = True,
    ) -> t.Callable:
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def websocket_route(self, path: str, name: str = None) -> t.Callable:
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def add_event_handler(self, event_type: str, func: t.Callable) -> None:
        """Not supported"""

    def on_event(self, event_type: str) -> t.Callable:
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def get_meta(self) -> t.Mapping:
        return self._meta
