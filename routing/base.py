import typing as t
from starlette.routing import Router, Mount, BaseRoute, Host, Route
from starletteapi.types import ASGIApp

from .route_definitions import RouteDefinitions
from ..compatible import DataMapper

if t.TYPE_CHECKING:
    from starletteapi.module import ApplicationModule
    from starletteapi.routing.operations import OperationBase
    from starletteapi.guard import GuardCanActivate


__all__ = ['ModuleRouter', 'AppRouter']


class AppRoutes(t.Sequence[BaseRoute]):
    __slots__ = ('_routes', '_app_module', '_served_routes')

    def __init__(self, app_module: 'ApplicationModule'):
        self._routes = []
        self._app_module = app_module
        self._served_routes = []
        self.reload_routes(force_build=False)

    @t.overload
    def __getitem__(self, i: int) -> BaseRoute: ...

    @t.overload
    def __getitem__(self, s: slice) -> BaseRoute: ...

    def __getitem__(self, i: int) -> BaseRoute:
        return self._served_routes.__getitem__(i)

    @t.overload
    def __setitem__(self, i: int, o: BaseRoute) -> None: ...

    @t.overload
    def __setitem__(self, s: slice, o: t.Iterable[BaseRoute]) -> None: ...

    def __setitem__(self, i: int, o: BaseRoute) -> None:
        self._routes.append(i)
        self.reload_routes(False)

    def __len__(self) -> int:
        return len(self._served_routes)

    def __iter__(self) -> t.Iterator[BaseRoute]:
        return iter(self._served_routes)

    def append(self, __item: t.Any) -> None:
        self.__setitem__(__item, __item)

    def get_routes(self) -> t.List[BaseRoute]:
        return self._served_routes.copy()

    def reload_routes(self, force_build: bool = True):
        self._served_routes = self._routes + self._app_module.get_routes(force_build=force_build)
        self._served_routes.sort(key=lambda e: getattr(e, 'path', getattr(e, 'host', '')))


class ModuleRouter(Mount):
    def __init__(
            self,
            path: str,
            name: str = None,
            tag: t.Optional[str] = None,
            description: t.Optional[str] = None,
            external_doc_description: t.Optional[str] = None,
            external_doc_url: t.Optional[str] = None,
            version: t.Union[t.List[str], str] = (),
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None
    ) -> None:
        super(ModuleRouter, self).__init__(path=path, routes=[], name=name)
        self._meta = DataMapper(
            tag=tag, external_doc_description=external_doc_description, description=description,
            external_doc_url=external_doc_url
        )
        self._route_guards: t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']] = guards or []
        self._version: t.Set[str] = set([version] if isinstance(version, str) else version)

        _route_definitions = RouteDefinitions(t.cast(list, self.routes))

        self.Get = _route_definitions.Get
        self.Post = _route_definitions.Post

        self.Delete = _route_definitions.Delete
        self.Patch = _route_definitions.Patch

        self.Put = _route_definitions.Put
        self.Options = _route_definitions.Options

        self.Trace = _route_definitions.Trace
        self.Head = _route_definitions.Head

        self.HttpRoute = _route_definitions.HttpRoute
        self.WsRoute = _route_definitions.WsRoute

    def get_meta(self) -> DataMapper:
        return self._meta

    def build_routes(self) -> None:
        for route in self.routes:
            route = t.cast('OperationBase', route)
            operation_meta = route.get_meta()

            if not operation_meta.route_versioning:
                operation_meta.update(route_versioning=self._version)
            if not operation_meta.route_guards:
                operation_meta.update(route_guards=self._route_guards)

            if isinstance(route, Route) and self._meta['tag']:
                tags = {self._meta['tag']}
                if operation_meta.tags:
                    tags.update(set(operation_meta.tags))
                operation_meta.update(tags=list(tags))


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
            lifespan=lifespan
        )
        self.routes = routes
        self._meta = DataMapper()
        _route_definitions = RouteDefinitions(t.cast(list, self.routes))

        self.Get = _route_definitions.Get
        self.Post = _route_definitions.Post

        self.Delete = _route_definitions.Delete
        self.Patch = _route_definitions.Patch

        self.Put = _route_definitions.Put
        self.Options = _route_definitions.Options

        self.Trace = _route_definitions.Trace
        self.Head = _route_definitions.Head

        self.HttpRoute = _route_definitions.HttpRoute
        self.WsRoute = _route_definitions.WsRoute

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

    def get_meta(self) -> DataMapper:
        return self._meta
