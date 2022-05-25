import typing as t

from starlette.routing import Router

from ellar.core.guard import GuardCanActivate

from ..router.module import ModuleRouterBase
from ..router.route_collections import ModuleRouteCollection
from .model import ControllerBase
from .route import ControllerRouteOperation
from .websocket.route import ControllerWebsocketRouteOperation


class ControllerRouter(ModuleRouterBase):
    routes: ModuleRouteCollection  # type:ignore

    def __init__(
        self,
        path: str,
        controller_type: t.Type[ControllerBase],
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]
        ] = None,
        include_in_schema: bool = True,
    ) -> None:
        app = Router()
        app.routes = ModuleRouteCollection()  # type:ignore
        super(ControllerRouter, self).__init__(
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
        self.controller_type = controller_type

    def _build_route_operation(  # type:ignore
        self, route: ControllerRouteOperation
    ) -> None:
        route.build_route_operation(
            path_prefix=self.path,
            name=self.name,
            include_in_schema=self.include_in_schema,
            controller_type=self.controller_type,
        )

    def _build_ws_route_operation(  # type:ignore
        self, route: ControllerWebsocketRouteOperation
    ) -> None:
        route.build_route_operation(
            path_prefix=self.path, name=self.name, controller_type=self.controller_type
        )
