import re
import typing as t
from functools import partial

from starletteapi.schema import RouteParameters, WsRouteParameters
from starletteapi.routing.operations import (
    Operation, WebsocketOperation, ControllerOperation, ControllerWebsocketOperation
)
from starletteapi.constants import (
    GET, POST, PUT, PATCH, HEAD, OPTIONS, TRACE, DELETE,
)


class RouteDefinitions:
    __slots__ = ('_routes', 'class_base_function_regex')

    def __init__(
            self, app_routes: t.Optional[t.List[t.Union[Operation, WebsocketOperation]]] = None
    ):
        self._routes: t.List[t.Union[Operation, WebsocketOperation]] = app_routes
        self.class_base_function_regex = re.compile("<\w+ (\w+)\.(\w+) at \w+>", re.IGNORECASE)

    @property
    def routes(self) -> t.Optional[t.List[t.Union[Operation, WebsocketOperation]]]:
        return self._routes

    def _get_http_operations_class(self, func: t.Callable) -> t.Type[Operation]:
        if self.class_base_function_regex.match(repr(func)):
            return ControllerOperation
        return Operation

    def _get_ws_operations_class(self, func: t.Callable) -> t.Type[WebsocketOperation]:
        if self.class_base_function_regex.match(repr(func)):
            return ControllerWebsocketOperation
        return WebsocketOperation

    def _get_operation(self, route_parameter: RouteParameters) -> Operation:
        _operation_class = self._get_http_operations_class(route_parameter.endpoint)
        _operation = _operation_class(**route_parameter.dict())
        if self._routes is not None:
            self._routes.append(_operation)
        return _operation

    def _get_ws_operation(self, ws_route_parameters: WsRouteParameters) -> Operation:
        _ws_operation_class = self._get_ws_operations_class(ws_route_parameters.endpoint)
        _operation = _ws_operation_class(**ws_route_parameters.dict())
        if self._routes:
            self._routes.append(_operation)
        return _operation

    def _get_decorator_or_operation(
            self, path: t.Union[str, t.Callable], endpoint_parameter_partial: t.Callable
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
        if callable(path):
            route_parameter = endpoint_parameter_partial(endpoint=t.cast(t.Callable, path), path="/")
            return self._get_operation(route_parameter=route_parameter)

        def _decorator(endpoint_handler: t.Callable) -> Operation:
            _route_parameter = endpoint_parameter_partial(endpoint=endpoint_handler, path=path)
            return self._get_operation(route_parameter=_route_parameter)

        return _decorator

    def Get(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t. List[t.Tuple[int, t.Type]], t. Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Post(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Put(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Patch(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Delete(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Head(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Options(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def Trace(
            self,
            path: str = "/",
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Union[Operation, t.Callable[..., Operation]]:
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

    def HttpRoute(
            self,
            path: str,
            methods: t.List[str],
            *,
            name: str = None,
            include_in_schema: bool = True,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            response: t.Union[t.Dict[int,t. Type], t.List[t.Tuple[int, t.Type]], t.Type, None] = None
    ) -> t.Callable:
        def _decorator(endpoint_handler: t.Callable) -> Operation:
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

    def WsRoute(
            self,
            path: str,
            *,
            name: str = None,
            encoding: str = "json",
            use_extra_handler: bool = False,
            extra_handler_type: t.Optional[t.Type] = None,
    ) -> t.Callable:
        def _decorator(endpoint_handler: t.Callable) -> WebsocketOperation:
            endpoint_parameter = WsRouteParameters(
                name=name,
                path=path,
                endpoint=endpoint_handler,
                encoding=encoding,
                use_extra_handler=use_extra_handler,
                extra_handler_type=extra_handler_type
            )
            return self._get_ws_operation(ws_route_parameters=endpoint_parameter)

        return _decorator

