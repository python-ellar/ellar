import functools
import typing as t

from ellar.common import ControllerBase, ModuleRouter
from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
)
from ellar.common.logging import request_logger
from ellar.common.types import TReceive, TScope, TSend
from ellar.reflect import reflect
from ellar.utils import get_unique_type
from starlette.middleware import Middleware
from starlette.routing import BaseRoute, Match, Route, Router
from starlette.routing import Mount as StarletteMount
from starlette.types import ASGIApp

from .route import RouteOperation
from .route_collections import RouteCollection

if t.TYPE_CHECKING:
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver


class EllarMount(StarletteMount):
    def __init__(
        self,
        path: str,
        *,
        routes: t.Optional[t.Sequence[t.Union[BaseRoute]]] = None,
        control_type: t.Optional[t.Type] = None,
        name: t.Optional[str] = None,
        include_in_schema: bool = False,
        middleware: t.Optional[t.Sequence[Middleware]] = None,
    ) -> None:
        app = Router()
        app.routes = RouteCollection(routes)  # type:ignore
        super().__init__(path=path, app=app, name=name, middleware=[])
        self.include_in_schema = include_in_schema
        self._control_type = control_type or get_unique_type("EllarMountDynamicType")

        self.user_middleware = [] if middleware is None else list(middleware)
        self._middleware_stack: t.Optional[ASGIApp] = None

    def build_middleware_stack(self) -> ASGIApp:
        app = self._app_handler
        for cls, args, kwargs in reversed(self.user_middleware):
            app = cls(app, *args, **kwargs)
        return app

    def get_control_type(self) -> t.Type[t.Any]:
        return self._control_type

    def add_route(
        self, route: t.Union[ControllerBase, ModuleRouter, BaseRoute, t.Callable]
    ) -> None:
        if (
            isinstance(route, type)
            and issubclass(route, ControllerBase)
            or isinstance(route, ModuleRouter)
        ):
            from ellar.core.router_builders.base import get_controller_builder_factory

            factory_builder = get_controller_builder_factory(type(route))
            factory_builder.check_type(route)
            mount = factory_builder.build(route)

            route = mount

        if not isinstance(route, BaseRoute) and self.get_control_type():
            reflect.define_metadata(
                CONTROLLER_CLASS_KEY, route, self.get_control_type()
            )

        self.routes.append(route)  # type:ignore[arg-type]

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        request_logger.debug(
            f"Matching URL Handler path={scope['path']} - '{self.__class__.__name__}'"
        )
        match, _child_scope = super().matches(scope)
        if match == Match.FULL:
            scope_copy = dict(scope)
            scope_copy.update(_child_scope)
            partial: t.Optional["RouteOperation"] = None
            partial_scope = {}

            for route in self.routes:
                # Determine if any route matches the incoming scope,
                # and hand over to the matching route if found.
                match, child_scope = route.matches(scope_copy)
                if match == Match.FULL:
                    _child_scope.update(child_scope)
                    _child_scope[str(self.get_control_type())] = route
                    return Match.FULL, _child_scope
                elif (
                    match == Match.PARTIAL
                    and partial is None
                    and isinstance(route, RouteOperation)
                ):
                    partial = route
                    partial_scope = dict(_child_scope)
                    partial_scope.update(child_scope)

            if partial:
                partial_scope[str(self.get_control_type())] = partial
                return Match.PARTIAL, partial_scope

        return Match.NONE, {}

    async def _app_handler(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        request_logger.debug(
            f"Executing Matched URL Handler, path={scope['path']} - '{self.__class__.__name__}'"
        )
        route = t.cast(t.Optional[Route], scope.get(str(self.get_control_type())))
        if route:
            del scope[str(self.get_control_type())]
            await route.handle(scope, receive, send)
        else:
            mount_router = t.cast(Router, self.app)
            await mount_router.default(scope, receive, send)

    async def handle(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if self._middleware_stack is None:
            self._middleware_stack = self.build_middleware_stack()
        await self._middleware_stack(scope, receive, send)


def router_default_decorator(func: ASGIApp) -> ASGIApp:
    @functools.wraps(func)
    async def _wrap(scope: TScope, receive: TReceive, send: TSend) -> None:
        version_scheme_resolver: "BaseAPIVersioningResolver" = t.cast(
            "BaseAPIVersioningResolver", scope[SCOPE_API_VERSIONING_RESOLVER]
        )
        if version_scheme_resolver and version_scheme_resolver.matched_any_route:
            version_scheme_resolver.raise_exception()

        await func(scope, receive, send)

    return _wrap


class ApplicationRouter(Router):
    routes: RouteCollection  # type: ignore

    def __init__(
        self,
        routes: t.Sequence[BaseRoute],
        redirect_slashes: bool = True,
        default: t.Optional[ASGIApp] = None,
        on_startup: t.Optional[t.Sequence[t.Callable]] = None,
        on_shutdown: t.Optional[t.Sequence[t.Callable]] = None,
        lifespan: t.Optional[t.Callable[[t.Any], t.AsyncContextManager]] = None,
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

    @t.no_type_check
    def add_route(
        self, route: t.Union[ControllerBase, ModuleRouter, BaseRoute, t.Callable]
    ) -> None:
        if (
            isinstance(route, type)
            and issubclass(route, ControllerBase)
            or isinstance(route, ModuleRouter)
        ):
            from ellar.core.router_builders.base import get_controller_builder_factory

            factory_builder = get_controller_builder_factory(type(route))
            factory_builder.check_type(route)
            mount = factory_builder.build(route)

            route = mount
        self.routes.append(route)

    def extend(self, routes: t.Sequence[t.Union[BaseRoute, t.Callable]]) -> None:
        for route in routes:
            self.add_route(route)

    def add_websocket_route(
        self, path: str, endpoint: t.Callable, name: t.Optional[str] = None
    ) -> None:  # pragma: no cover
        """Not supported"""

    def route(
        self,
        path: str,
        methods: t.Optional[t.List[str]] = None,
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> t.Callable:  # pragma: no cover
        def decorator(func: t.Callable) -> t.Callable:
            """Not supported"""
            return func

        return decorator

    def websocket_route(
        self, path: str, name: t.Optional[str] = None
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
        self, path: str, app: ASGIApp, name: t.Optional[str] = None
    ) -> None:  # pragma: no cover
        raise Exception(
            "Not supported. Use mount external asgi app in any @Module decorated "
            "class in `routers` parameter. eg @Module(routers=[ellar.core.mount(my_asgi_app)]"
        )

    def host(
        self, host: str, app: ASGIApp, name: t.Optional[str] = None
    ) -> None:  # pragma: no cover
        raise Exception(
            "Not supported. Use host external asgi app in any @Module decorated "
            "class in `routers` parameter. eg @Module(routers=[ellar.core.host(my_asgi_app)]"
        )
