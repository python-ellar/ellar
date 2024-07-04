import typing as t

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    GUARDS_KEY,
    NESTED_ROUTERS_KEY,
    VERSIONING_KEY,
)
from ellar.common.models import GuardCanActivate
from ellar.common.models.controller import NestedRouterInfo
from ellar.di import injectable
from ellar.reflect import reflect
from ellar.utils import get_unique_type
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
        self._control_type: t.Type[t.Any] = injectable(get_unique_type())  # type:ignore[assignment]
        self._kwargs = {
            "path": path,
            "name": name,
            "include_in_schema": include_in_schema,
            "control_type": self._control_type,
            "middleware": middleware,
        }

        self._pre_build_routes: t.List[t.Union[RouteParameters, WsRouteParameters]] = []

        reflect.define_metadata(GUARDS_KEY, guards or [], self.control_type)
        reflect.define_metadata(VERSIONING_KEY, set(version or []), self.control_type)

    @property
    def control_type(self) -> t.Type[t.Any]:
        return self._control_type

    def add_router(
        self,
        router: t.Union["ModuleRouter", t.Type["ControllerBase"]],
        prefix: t.Optional[str] = None,
    ) -> None:
        if prefix:
            assert prefix.startswith("/"), "'prefix' must start with '/'"
        reflect.define_metadata(
            NESTED_ROUTERS_KEY,
            [NestedRouterInfo(prefix=prefix, router=router)],
            self.control_type,
        )

    def get_mount_init(self) -> t.Dict[str, t.Any]:
        return self._kwargs.copy()

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
            # this is needed to happen before adding operation to router else we lose ability to
            # get extra information about operation that is set on the router.
            reflect.define_metadata(
                CONTROLLER_CLASS_KEY, self.control_type, operation_handler
            )
