import typing as t
import uuid

from starlette.routing import BaseRoute, Match, Mount as StarletteMount, Route, Router
from starlette.types import ASGIApp

from ellar.compatible import AttributeDict
from ellar.constants import (
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    GUARDS_KEY,
    NOT_SET,
    OPENAPI_KEY,
    VERSIONING_KEY,
)
from ellar.core.controller import ControllerBase
from ellar.core.routing.route import RouteOperation
from ellar.core.routing.websocket.route import WebsocketRouteOperation
from ellar.reflect import reflect
from ellar.types import TReceive, TScope, TSend

from ..operation_definitions import OperationDefinitions
from .route_collections import RouteCollection

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.guard import GuardCanActivate

__all__ = ["ModuleMount", "ModuleRouter", "controller_router_factory"]


def controller_router_factory(
    controller: t.Union[t.Type[ControllerBase], t.Any]
) -> "ModuleMount":
    openapi = reflect.get_metadata(CONTROLLER_METADATA.OPENAPI, controller) or dict()
    routes = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, controller) or []
    app = Router()
    app.routes = RouteCollection(routes)  # type:ignore

    include_in_schema = reflect.get_metadata_or_raise_exception(
        CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, controller
    )
    router = ModuleMount(
        app=app,
        path=reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.PATH, controller
        ),
        name=reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.NAME, controller
        ),
        version=reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.VERSION, controller
        ),
        guards=reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.GUARDS, controller
        ),
        include_in_schema=include_in_schema if include_in_schema is not None else True,
        **openapi,
    )
    return router


class ModuleMount(StarletteMount):
    def __init__(
        self,
        path: str,
        app: ASGIApp = None,
        routes: t.Sequence[BaseRoute] = None,
        name: str = None,
        tag: str = NOT_SET,
        description: str = None,
        external_doc_description: str = None,
        external_doc_url: str = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]] = None,
        include_in_schema: bool = False,
    ) -> None:
        super(ModuleMount, self).__init__(path=path, routes=routes, name=name, app=app)
        self.include_in_schema = include_in_schema
        self._meta: AttributeDict = AttributeDict(
            tag=name or "Module Router" if tag is NOT_SET else tag,
            external_doc_description=external_doc_description,
            description=description,
            external_doc_url=external_doc_url,
        )
        self._route_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate", t.Any]
        ] = (guards or [])
        self._version = set(version or [])
        self._build: bool = False
        self._current_found_route_key = f"{uuid.uuid4().hex:4}_ModuleMountRoute"

    def get_meta(self) -> t.Mapping:
        return self._meta

    def get_tag(self) -> t.Dict:
        external_doc = None
        if self._meta.external_doc_url:
            external_doc = dict(
                url=self._meta.external_doc_url,
                description=self._meta.external_doc_description,
            )

        if self._meta.tag:
            return dict(
                name=self._meta.tag,
                description=self._meta.description,
                externalDocs=external_doc,
            )
        return dict()

    def _build_route_operation(self, route: RouteOperation) -> None:
        route.build_route_operation(
            path_prefix=self.path,
            name=self.name,
            include_in_schema=self.include_in_schema,
        )

    def _build_ws_route_operation(self, route: WebsocketRouteOperation) -> None:
        route.build_route_operation(path_prefix=self.path, name=self.name)

    def build_child_routes(self, flatten: bool = False) -> None:
        for route in self.routes:
            _route: RouteOperation = t.cast(RouteOperation, route)

            route_versioning = reflect.get_metadata(VERSIONING_KEY, _route.endpoint)
            route_guards = reflect.get_metadata(GUARDS_KEY, _route.endpoint)

            if not route_versioning:
                reflect.define_metadata(
                    VERSIONING_KEY,
                    self._version,
                    _route.endpoint,
                    default_value=set(),
                )
            if not route_guards:
                reflect.define_metadata(
                    GUARDS_KEY,
                    self._route_guards,
                    _route.endpoint,
                    default_value=[],
                )
            if flatten:
                openapi = (
                    reflect.get_metadata(OPENAPI_KEY, _route.endpoint)
                    or AttributeDict()
                )
                if isinstance(_route, Route):
                    if not openapi.tags and self._meta.get("tag"):
                        tags = {self._meta.get("tag")}
                        tags.update(set(openapi.tags or []))
                        openapi.update(tags=list(tags))
                        reflect.define_metadata(OPENAPI_KEY, openapi, _route.endpoint)
                    self._build_route_operation(_route)
                elif isinstance(_route, WebsocketRouteOperation):
                    self._build_ws_route_operation(_route)

    def get_flatten_routes(self) -> t.List[BaseRoute]:
        if not self._build:
            self.build_child_routes(flatten=True)
            self._build = True
        return list(self.routes)

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        match, _child_scope = super().matches(scope)
        if match == Match.FULL:
            scope_copy = dict(scope)
            scope_copy.update(_child_scope)
            partial: t.Optional[RouteOperation] = None
            partial_scope = dict()

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
        route = t.cast(t.Optional[Route], scope.get(self._current_found_route_key))
        if route:
            del scope[self._current_found_route_key]
            await route.handle(scope, receive, send)
            return
        mount_router = t.cast(Router, self.app)
        await mount_router.default(scope, receive, send)


class ModuleRouter(ModuleMount):
    operation_definition_class: t.Type[OperationDefinitions] = OperationDefinitions
    routes: RouteCollection  # type:ignore

    def __init__(
        self,
        path: str = "",
        name: str = None,
        tag: str = NOT_SET,
        description: str = None,
        external_doc_description: str = None,
        external_doc_url: str = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]] = None,
        include_in_schema: bool = True,
    ) -> None:
        app = Router()
        app.routes = RouteCollection()  # type:ignore

        super(ModuleRouter, self).__init__(
            path=path,
            tag=tag,
            name=name,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            version=version,
            guards=guards,
            include_in_schema=include_in_schema,
            app=app,
        )
        _route_definitions = self.operation_definition_class(t.cast(list, self.routes))

        self.get = _route_definitions.get
        self.post = _route_definitions.post

        self.delete = _route_definitions.delete
        self.patch = _route_definitions.patch

        self.put = _route_definitions.put
        self.options = _route_definitions.options

        self.trace = _route_definitions.trace
        self.head = _route_definitions.head

        self.http_route = _route_definitions.http_route
        self.ws_route = _route_definitions.ws_route
