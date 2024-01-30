import functools
import typing as t
import uuid

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    GUARDS_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
    VERSIONING_KEY,
)
from ellar.common.logging import request_logger
from ellar.common.models import GuardCanActivate
from ellar.common.types import TReceive, TScope, TSend
from ellar.common.utils import get_unique_control_type
from ellar.reflect import reflect
from starlette.middleware import Middleware
from starlette.routing import BaseRoute, Match, Route, Router
from starlette.routing import Mount as StarletteMount
from starlette.types import ASGIApp

from .operation_definitions import OperationDefinitions
from .route import RouteOperation
from .route_collections import RouteCollection
from .schema import RouteParameters, WsRouteParameters
from .utils import build_route_handler

if t.TYPE_CHECKING:
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver


class ModuleMount(StarletteMount):
    def __init__(
        self,
        path: str,
        control_type: t.Type,
        app: t.Optional[ASGIApp] = None,
        routes: t.Optional[t.Sequence[BaseRoute]] = None,
        name: t.Optional[str] = None,
        include_in_schema: bool = False,
        *,
        middleware: t.Optional[t.Sequence[Middleware]] = None,
    ) -> None:
        super(ModuleMount, self).__init__(
            path=path, routes=routes, name=name, app=app, middleware=middleware
        )
        self.include_in_schema = include_in_schema
        self._current_found_route_key = f"{uuid.uuid4().hex:4}_ModuleMountRoute"
        self._control_type = control_type

    def get_control_type(self) -> t.Type:
        return self._control_type

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        request_logger.debug(
            f"Matching URL Handler path={scope['path']} - '{self.__class__.__name__}'"
        )
        match, _child_scope = super().matches(scope)
        if match == Match.FULL:
            scope_copy = dict(scope)
            scope_copy.update(_child_scope)
            partial: t.Optional[RouteOperation] = None
            partial_scope = {}

            for route in self.routes:
                # Determine if any route matches the incoming scope,
                # and hand over to the matching route if found.
                match, child_scope = route.matches(scope_copy)
                if match == Match.FULL:
                    _child_scope.update(child_scope)
                    _child_scope[self._current_found_route_key] = route
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
                partial_scope[self._current_found_route_key] = partial
                return Match.PARTIAL, partial_scope

        return Match.NONE, {}

    async def handle(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        request_logger.debug(
            f"Executing Matched URL Handler, path={scope['path']} - '{self.__class__.__name__}'"
        )
        route = t.cast(t.Optional[Route], scope.get(self._current_found_route_key))
        if route:
            del scope[self._current_found_route_key]
            await route.handle(scope, receive, send)
        else:
            mount_router = t.cast(Router, self.app)
            await mount_router.default(scope, receive, send)


class ModuleRouter(OperationDefinitions, ModuleMount):
    routes: RouteCollection  # type:ignore

    def __init__(
        self,
        path: str = "",
        name: t.Optional[str] = None,
        version: t.Union[t.Sequence[str], str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        include_in_schema: bool = True,
    ) -> None:
        app = Router()
        app.routes = RouteCollection()  # type:ignore

        super(ModuleRouter, self).__init__(
            path=path,
            name=name,
            include_in_schema=include_in_schema,
            app=app,
            control_type=get_unique_control_type(),
        )
        reflect.define_metadata(GUARDS_KEY, guards or [], self.get_control_type())
        reflect.define_metadata(
            VERSIONING_KEY, set(version or []), self.get_control_type()
        )
        self._pre_build_routes: t.List[t.Union[RouteParameters, WsRouteParameters]] = []

    def get_pre_build_routes(
        self,
    ) -> t.List[t.Union[RouteParameters, WsRouteParameters]]:
        return self._pre_build_routes

    def clear_pre_build_routes(self) -> None:
        self._pre_build_routes.clear()

    def _get_operation(self, route_parameter: RouteParameters) -> t.Callable:
        endpoint = super()._get_operation(route_parameter)
        self._pre_build_routes.append(route_parameter)
        self._set_other_router_attributes(endpoint)
        return endpoint

    def _get_ws_operation(self, ws_route_parameters: WsRouteParameters) -> t.Callable:
        endpoint = super()._get_ws_operation(ws_route_parameters)
        self._pre_build_routes.append(ws_route_parameters)
        self._set_other_router_attributes(endpoint)
        return endpoint

    def _set_other_router_attributes(self, operation_handler: t.Callable) -> None:
        if not reflect.has_metadata(CONTROLLER_CLASS_KEY, operation_handler):
            # this is need to happen before adding operation to router else we lose ability to
            # get extra information about operation that is set on the router.
            reflect.define_metadata(
                CONTROLLER_CLASS_KEY, self.get_control_type(), operation_handler
            )


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

    def append(self, item: t.Union[BaseRoute, t.Callable]) -> None:
        _items: t.Any = build_route_handler(item)
        if _items:
            self.routes.extend(_items)

    def extend(self, routes: t.Sequence[t.Union[BaseRoute, t.Callable]]) -> None:
        for route in routes:
            self.append(route)

    def add_route(
        self,
        path: str,
        endpoint: t.Callable,
        methods: t.Optional[t.List[str]] = None,
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:  # pragma: no cover
        """Not supported"""

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
    ) -> None:  # pragma: nocover
        """Not supported"""

    def host(
        self, host: str, app: ASGIApp, name: t.Optional[str] = None
    ) -> None:  # pragma: no cover
        """Not supported"""
