import functools
import typing as t

from ellar.common.constants import (
    MODULE_COMPONENT,
    SCOPE_API_VERSIONING_RESOLVER,
)
from ellar.common.logging import logger, request_logger
from ellar.common.types import TReceive, TScope, TSend
from ellar.reflect import fail_silently, reflect
from starlette._utils import get_route_path
from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.responses import RedirectResponse
from starlette.routing import BaseRoute, Match, Route, Router
from starlette.routing import Mount as StarletteMount
from starlette.types import ASGIApp

from .route import RouteOperation
from .route_collections import RouteCollection

if t.TYPE_CHECKING:
    from ellar.core.modules import ModuleRefBase
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver


class EllarControllerMount(StarletteMount):
    """
    Controller and ModuleRouter Object compiles to this Class at runtime
    """

    def __init__(
        self,
        path: str,
        *,
        routes: t.Optional[t.Sequence[t.Union[BaseRoute]]] = None,
        name: t.Optional[str] = None,
        include_in_schema: bool = False,
        middleware: t.Optional[t.Sequence[Middleware]] = None,
    ) -> None:
        app = Router()
        app.routes = RouteCollection(routes)  # type:ignore
        super().__init__(path=path, app=app, name=name, middleware=[])
        self.include_in_schema = include_in_schema

        self.middleware = [] if middleware is None else list(middleware)
        self._middleware_stack: t.Optional[ASGIApp] = None

    @functools.cached_property
    def _lookup_key(self) -> str:
        return f"EllarControllerMountRoute_{id(self)}"

    def build_middleware_stack(self) -> ASGIApp:
        app = self._app_handler
        for cls, args, kwargs in reversed(self.middleware):
            try:
                app = cls(app, *args, **kwargs)
            except Exception as ex:
                logger.exception(f"Unable to setup middleware='{cls}'")
                raise ex
        return app

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
                    _child_scope[self._lookup_key] = route
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
                partial_scope[self._lookup_key] = partial
                return Match.PARTIAL, partial_scope

        return Match.NONE, {}

    async def _app_handler(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        request_logger.debug(
            f"Executing Matched URL Handler, path={scope['path']} - '{self.__class__.__name__}'"
        )
        route = t.cast(t.Optional[Route], scope.get(self._lookup_key))
        if route:
            del scope[self._lookup_key]
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

    def _get_route_handler(
        self, scope: TScope
    ) -> t.Optional[t.Union[BaseRoute, RedirectResponse]]:
        partial = None
        partial_scope: t.Dict = {}

        for route in self.routes:
            # Determine if any route matches the incoming scope,
            # and hand over to the matching route if found.
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                scope.update(child_scope)
                return route

            elif match == Match.PARTIAL and partial is None:
                partial = route
                partial_scope = dict(child_scope)

        if partial is not None:
            #  Handle partial matches. These are cases where an endpoint is
            # able to handle the request, but is not a preferred option.
            # We use this in particular to deal with "405 Method Not Allowed".
            scope.update(partial_scope, partial=True)
            return partial

        route_path = get_route_path(scope)
        if scope["type"] == "http" and self.redirect_slashes and route_path != "/":
            redirect_scope = dict(scope)
            if route_path.endswith("/"):
                redirect_scope["path"] = redirect_scope["path"].rstrip("/")
            else:
                redirect_scope["path"] = redirect_scope["path"] + "/"

            for route in self.routes:
                match, child_scope = route.matches(redirect_scope)
                if match != Match.NONE:
                    redirect_url = URL(scope=redirect_scope)
                    return RedirectResponse(url=str(redirect_url))

        return None

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        assert scope["type"] in ("http", "websocket", "lifespan")

        if "router" not in scope:
            scope["router"] = self

        if scope["type"] == "lifespan":
            return await self.lifespan(scope, receive, send)

        route = self._get_route_handler(scope)

        if route is None:
            return await self.default(scope, receive, send)

        if isinstance(route, RedirectResponse):
            return await route(scope, receive, send)

        module_ref: t.Optional["ModuleRefBase"] = t.cast(
            t.Optional["ModuleRefBase"],
            fail_silently(reflect.get_metadata_search_safe, MODULE_COMPONENT, route),
        )
        if scope.get("partial", False) is False and module_ref:
            async with module_ref.module_context.context(route) as module_context:
                return await module_context.handle(scope, receive, send)

        await route.handle(scope, receive, send)

    # @t.no_type_check
    def add(self, route: t.Union[BaseRoute, t.Callable]) -> None:
        if not isinstance(route, BaseRoute):
            raise RuntimeError(f"Invalid type passed to router - {route}")
        self.routes.append(route)

    def extend(self, routes: t.Sequence[t.Union[BaseRoute, t.Callable]]) -> None:
        for route in routes:
            self.add(route)

    def mount(
        self, path: str, app: ASGIApp, name: t.Optional[str] = None
    ) -> None:  # pragma: no cover
        logger.info(
            "Not supported. Use mount external asgi app in any @Module decorated "
            "class in `routers` parameter. eg @Module(routers=[ellar.core.mount(my_asgi_app)]"
        )
        return super().mount(path=path, app=app, name=name)

    def host(
        self, host: str, app: ASGIApp, name: t.Optional[str] = None
    ) -> None:  # pragma: no cover
        logger.info(
            "Not supported. Use host external asgi app in any @Module decorated "
            "class in `routers` parameter. eg @Module(routers=[ellar.core.host(my_asgi_app)]"
        )
        return super().host(host=host, app=app, name=name)
