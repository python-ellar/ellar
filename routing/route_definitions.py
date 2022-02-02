from functools import partial
from typing import Optional, List, Callable, Union, Dict, Type, Tuple, cast

from starletteapi.schema import RouteParameters, WsRouteParameters
from starletteapi.routing.operations import (
    Operation, WebsocketOperation
)
from starletteapi.constants import (
    GET, POST, PUT, PATCH, HEAD, OPTIONS, TRACE, DELETE,
)


class RouteDefinitions:
    def __init__(
            self,
            http_operations_class: Type[Operation],
            web_socket_operations_class: Type[WebsocketOperation],
            app_routes: Optional[List[Union[Operation, WebsocketOperation]]] = None
    ):
        self.http_operations_class = http_operations_class
        self.websocket_operation_class = web_socket_operations_class
        self._routes: List[Union[Operation, WebsocketOperation]] = app_routes

    @property
    def routes(self) -> Optional[List[Union[Operation, WebsocketOperation]]]:
        return self._routes

    def _get_operation(self, route_parameter: RouteParameters) -> Operation:
        _operation = self.http_operations_class(route_parameter=route_parameter)
        if self._routes is not None and isinstance(self._routes, list):
            self._routes.append(_operation)
        return _operation

    def _get_ws_operation(self, ws_route_parameters: WsRouteParameters) -> Operation:
        _operation = self.websocket_operation_class(ws_route_parameters=ws_route_parameters)
        if self._routes is not None and isinstance(self._routes, list):
            self._routes.append(_operation)
        return _operation

    def _get_decorator_or_operation(
            self, path: Union[str, Callable], endpoint_parameter_partial: Callable
    ) -> Union[Operation, Callable[..., Operation]]:
        if callable(path):
            route_parameter = endpoint_parameter_partial(endpoint=cast(Callable, path), path="/")
            return self._get_operation(route_parameter=route_parameter)

        def _decorator(endpoint_handler: Callable) -> Operation:
            _route_parameter = endpoint_parameter_partial(endpoint=endpoint_handler, path=path)
            return self._get_operation(route_parameter=_route_parameter)

        return _decorator

    def get(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [GET]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def post(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [POST]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def put(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [PUT]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def patch(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [PATCH]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def delete(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [DELETE]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def head(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [HEAD]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def options(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [OPTIONS]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def trace(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Union[Operation, Callable[..., Operation]]:
        methods = [TRACE]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            response=response
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def route(
            self,
            path: str,
            methods: List[str],
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: Optional[str] = None,
            summary: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None,
            deprecated: Optional[bool] = None,
            response: Union[Dict[int, Type], List[Tuple[int, Type]], Type, None] = None
    ) -> Callable:
        def _decorator(endpoint_handler: Callable) -> Operation:
            endpoint_parameter = RouteParameters(
                name=name,
                path=path,
                methods=methods,
                operation_id=operation_id,
                summary=summary,
                description=description,
                tags=tags,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
                response=response,
                endpoint=endpoint_handler
            )
            return self._get_operation(route_parameter=endpoint_parameter)

        return _decorator

    def websocket(
            self,
            path: str,
            *,
            name: str = None,
    ) -> Callable:
        def _decorator(endpoint_handler: Callable) -> WebsocketOperation:
            endpoint_parameter = WsRouteParameters(
                name=name,
                path=path,
                endpoint=endpoint_handler
            )
            return self._get_ws_operation(ws_route_parameters=endpoint_parameter)

        return _decorator

