import typing as t

from ellar.common import constants
from ellar.common.models import GuardCanActivate
from ellar.common.models.controller import NestedRouterInfo
from ellar.reflect import reflect
from starlette.middleware import Middleware

from .base import OperationDefinitions
from .schema import RouteParameters, WsRouteParameters

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import ControllerBase


class ModuleRouter(OperationDefinitions):
    def __init__(
        self,
        path: str = "",
        name: t.Optional[str] = None,
        version: t.Union[t.Sequence[str], str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        include_in_schema: bool = True,
        middleware: t.Optional[t.Sequence[Middleware]] = None,
    ) -> None:
        # self._control_type: t.Type[t.Any] = injectable(get_unique_type())  # type:ignore[assignment]
        self.path = path
        self.name = name
        self.include_in_schema = include_in_schema
        self.middleware = list(middleware) if middleware else []

        reflect.define_metadata(constants.GUARDS_KEY, guards or [], self)
        reflect.define_metadata(constants.VERSIONING_KEY, set(version or []), self)

    def __repr__(self) -> str:
        return f"<ModuleRouter path={self.path} name={self.name}>"

    def add_router(
        self,
        router: t.Union["ModuleRouter", t.Type["ControllerBase"]],
        prefix: t.Optional[str] = None,
    ) -> None:
        if prefix:
            assert prefix.startswith("/"), "'prefix' must start with '/'"

        reflect.define_metadata(
            constants.NESTED_ROUTERS_KEY,
            [NestedRouterInfo(prefix=prefix, router=router)],
            self,
        )

    def _get_operation(self, route_parameter: RouteParameters) -> t.Callable:
        endpoint = super()._get_operation(route_parameter)
        reflect.define_metadata(
            constants.ROUTER_PRE_BUILD_ROUTES, [route_parameter], self
        )
        # self._set_other_router_attributes(ensure_function(endpoint))
        reflect.define_metadata("ROUTER_REFLECT_KEY", self, endpoint)
        return endpoint

    def _get_ws_operation(self, ws_route_parameters: WsRouteParameters) -> t.Callable:
        endpoint = super()._get_ws_operation(ws_route_parameters)
        reflect.define_metadata(
            constants.ROUTER_PRE_BUILD_ROUTES, [ws_route_parameters], self
        )
        # self._set_other_router_attributes(ensure_function(endpoint))
        reflect.define_metadata("ROUTER_REFLECT_KEY", self, endpoint)
        return endpoint
