import typing as t

from starlette.routing import BaseRoute, Host, Mount, Route, Router

from architek.types import ASGIApp

from ..compatible import DataMapper
from .route_definitions import RouteDefinitions

if t.TYPE_CHECKING:
    from architek.guard import GuardCanActivate
    from architek.module import ApplicationModule
    from architek.routing.operations import OperationBase


__all__ = ["ModuleRouter", "AppRouter", "AppRoutes"]


class AppRoutes(t.Sequence[BaseRoute]):
    __slots__ = ("_routes", "_app_module", "_served_routes")

    def __init__(self, app_module: "ApplicationModule") -> None:
        self._routes: t.List[BaseRoute] = []
        self._app_module = app_module
        self._served_routes: t.List[BaseRoute] = []
        self.reload_routes(force_build=False)

    @t.no_type_check
    def __getitem__(self, i: int) -> BaseRoute:
        return self._served_routes.__getitem__(i)

    def __setitem__(self, i: int, o: BaseRoute) -> None:
        self._routes.append(o)
        self.reload_routes(False)

    def __len__(self) -> int:
        return len(self._served_routes)

    def __iter__(self) -> t.Iterator[BaseRoute]:
        return iter(self._served_routes)

    def append(self, __item: t.Any) -> None:
        self.__setitem__(__item, __item)

    def get_routes(self) -> t.List[BaseRoute]:
        return self._served_routes.copy()

    def reload_routes(self, force_build: bool = True) -> None:
        self._served_routes = self._routes + self._app_module.get_routes(
            force_build=force_build
        )
        # TODO: flatten the routes for faster look up
        self._served_routes.sort(
            key=lambda e: getattr(e, "path", getattr(e, "host", ""))
        )


class ModuleRouter(Mount):
    def __init__(
        self,
        path: str,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]] = None,
    ) -> None:
        super(ModuleRouter, self).__init__(path=path, routes=[], name=name)
        self._meta: t.Mapping = DataMapper(
            tag=tag,
            external_doc_description=external_doc_description,
            description=description,
            external_doc_url=external_doc_url,
        )
        self._route_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
        ] = (guards or [])
        self._version: t.Set[str] = set(
            [version] if isinstance(version, str) else version
        )

        _route_definitions = RouteDefinitions(t.cast(list, self.routes))

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

    def get_meta(self) -> t.Mapping:
        return self._meta

    def build_routes(self) -> None:
        for route in self.routes:
            _route: OperationBase = t.cast("OperationBase", route)
            operation_meta = _route.get_meta()

            if not operation_meta.route_versioning:
                operation_meta.update(route_versioning=self._version)
            if not operation_meta.route_guards:
                operation_meta.update(route_guards=self._route_guards)

            if isinstance(_route, Route) and self._meta.get("tag"):
                tags = {self._meta["tag"]}
                if operation_meta.openapi.tags:
                    tags.update(set(operation_meta.openapi.tags))
                operation_meta.openapi.update(tags=list(tags))


class AppRouter(Router):
    def __init__(
        self,
        routes: AppRoutes,
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
        self.routes: AppRoutes = routes  # type: ignore
        self._meta: t.Mapping = DataMapper()
        _route_definitions = RouteDefinitions(t.cast(list, self.routes))

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
        route = Mount(path, app=app, name=name)
        self.routes.append(route)

    def host(self, host: str, app: ASGIApp, name: str = None) -> None:
        route = Host(host, app=app, name=name)
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
