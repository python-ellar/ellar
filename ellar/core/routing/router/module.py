import typing as t
import uuid

from starlette.routing import BaseRoute, Match, Mount as StarletteMount, Route, Router
from starlette.types import ASGIApp

from ellar.compatible import AttributeDict
from ellar.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    GUARDS_KEY,
    NOT_SET,
    OPERATION_ENDPOINT_KEY,
    VERSIONING_KEY,
)
from ellar.core.controller import ControllerBase
from ellar.core.routing.route import RouteOperation
from ellar.core.schema import RouteParameters, WsRouteParameters
from ellar.helper import get_unique_control_type
from ellar.reflect import reflect
from ellar.types import TReceive, TScope, TSend

from ..operation_definitions import (
    OperationDefinitions,
    TOperation,
    TWebsocketOperation,
)
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

    reflect.get_metadata_or_raise_exception(VERSIONING_KEY, controller)
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
        include_in_schema=include_in_schema if include_in_schema is not None else True,
        control_type=controller,
        **openapi,
    )
    return router


class ModuleMount(StarletteMount):
    def __init__(
        self,
        path: str,
        control_type: t.Type,
        app: ASGIApp = None,
        routes: t.Sequence[BaseRoute] = None,
        name: str = None,
        tag: t.Optional[str] = NOT_SET,
        description: str = None,
        external_doc_description: str = None,
        external_doc_url: str = None,
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
        self._current_found_route_key = f"{uuid.uuid4().hex:4}_ModuleMountRoute"
        self._control_type = control_type

    def get_control_type(self) -> t.Type:
        return self._control_type

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


class ModuleRouter(OperationDefinitions, ModuleMount):
    routes: RouteCollection  # type:ignore

    def __init__(
        self,
        path: str = "",
        name: str = None,
        tag: str = NOT_SET,
        description: str = None,
        external_doc_description: str = None,
        external_doc_url: str = None,
        version: t.Union[t.Sequence[str], str] = (),
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
            include_in_schema=include_in_schema,
            app=app,
            control_type=get_unique_control_type(),
        )
        reflect.define_metadata(GUARDS_KEY, guards or [], self.get_control_type())
        reflect.define_metadata(
            VERSIONING_KEY, set(version or []), self.get_control_type()
        )

    def _get_operation(self, route_parameter: RouteParameters) -> TOperation:
        _operation_class = self._get_http_operations_class(route_parameter.endpoint)
        _operation = _operation_class(**route_parameter.dict())
        setattr(route_parameter.endpoint, OPERATION_ENDPOINT_KEY, True)
        self._set_other_router_attributes(_operation)
        return _operation

    def _get_ws_operation(
        self, ws_route_parameters: WsRouteParameters
    ) -> TWebsocketOperation:
        _ws_operation_class = self._get_ws_operations_class(
            ws_route_parameters.endpoint
        )
        _operation = _ws_operation_class(**ws_route_parameters.dict())
        setattr(ws_route_parameters.endpoint, OPERATION_ENDPOINT_KEY, True)
        self._set_other_router_attributes(_operation)
        return _operation

    def _set_other_router_attributes(
        self, operation: t.Union[TWebsocketOperation, TOperation]
    ) -> None:
        if not reflect.has_metadata(CONTROLLER_CLASS_KEY, operation.endpoint):
            # this is need to happen before adding operation to router else we lose ability to
            # get extra information about operation that is set on the router.
            reflect.define_metadata(
                CONTROLLER_CLASS_KEY, self.get_control_type(), operation.endpoint
            )

        self.app.routes.append(operation)  # type:ignore
