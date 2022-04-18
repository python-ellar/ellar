import re
import typing as t
from functools import partial

from architek.constants import DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, TRACE
from architek.routing.operations import (
    Operation,
    OperationDecorator,
    RouteOperationDecorator,
    WebsocketOperation,
    WebsocketOperationDecorator,
)
from architek.schema import RouteParameters, WsRouteParameters
from architek.types import TCallable

TOperation = t.Union[Operation, RouteOperationDecorator]
TWebsocketOperation = t.Union[WebsocketOperation, WebsocketOperationDecorator]


class RouteDefinitions:
    __slots__ = ("_routes", "class_base_function_regex")

    def __init__(
        self,
        app_routes: t.List[t.Union[Operation, WebsocketOperation]] = None,
    ):
        self._routes = app_routes
        self.class_base_function_regex = re.compile(
            "<\\w+ (\\w+)\\.(\\w+) at \\w+>", re.IGNORECASE
        )

    @property
    def routes(self) -> t.List[t.Union[Operation, WebsocketOperation]]:
        return self._routes or []

    def _get_http_operations_class(self, func: t.Callable) -> t.Type[TOperation]:
        if self.class_base_function_regex.match(repr(func)):
            return RouteOperationDecorator
        return Operation

    def _get_ws_operations_class(self, func: t.Callable) -> t.Type[TWebsocketOperation]:
        if self.class_base_function_regex.match(repr(func)):
            return WebsocketOperationDecorator
        return WebsocketOperation

    def _get_operation(self, route_parameter: RouteParameters) -> TOperation:
        _operation_class = self._get_http_operations_class(route_parameter.endpoint)
        _operation = _operation_class(**route_parameter.dict())
        if self._routes is not None and not isinstance(_operation, OperationDecorator):
            self._routes.append(_operation)
        return _operation

    def _get_ws_operation(
        self, ws_route_parameters: WsRouteParameters
    ) -> TWebsocketOperation:
        _ws_operation_class = self._get_ws_operations_class(
            ws_route_parameters.endpoint
        )
        _operation = _ws_operation_class(**ws_route_parameters.dict())
        if self._routes is not None and not isinstance(_operation, OperationDecorator):
            self._routes.append(_operation)
        return _operation

    def _get_decorator_or_operation(
        self, path: t.Union[str, t.Callable], endpoint_parameter_partial: t.Callable
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        if callable(path):
            route_parameter = endpoint_parameter_partial(endpoint=path, path="/")
            return self._get_operation(route_parameter=route_parameter)  # type: ignore

        def _decorator(endpoint_handler: t.Callable) -> TOperation:
            _route_parameter = endpoint_parameter_partial(
                endpoint=endpoint_handler, path=path
            )
            return self._get_operation(route_parameter=_route_parameter)

        return _decorator

    def get(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [GET]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def post(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [POST]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def put(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [PUT]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def patch(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [PATCH]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def delete(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [DELETE]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def head(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [HEAD]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def options(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [OPTIONS]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def trace(
        self,
        path: str = "/",
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        methods = [TRACE]
        endpoint_parameter_partial = partial(
            RouteParameters,
            name=name,
            methods=methods,
            include_in_schema=include_in_schema,
            response=response,
        )
        return self._get_decorator_or_operation(path, endpoint_parameter_partial)

    def http_route(
        self,
        path: str,
        methods: t.List[str],
        *,
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        def _decorator(endpoint_handler: t.Callable) -> TOperation:
            endpoint_parameter = RouteParameters(
                name=name,
                path=path,
                methods=methods,
                include_in_schema=include_in_schema,
                response=response,
                endpoint=endpoint_handler,
            )
            return self._get_operation(route_parameter=endpoint_parameter)

        return _decorator

    def ws_route(
        self,
        path: str,
        *,
        name: str = None,
        encoding: str = "json",
        use_extra_handler: bool = False,
        extra_handler_type: t.Optional[t.Type] = None,
    ) -> t.Callable[[TCallable], t.Union[TCallable, TWebsocketOperation]]:
        def _decorator(endpoint_handler: t.Callable) -> TWebsocketOperation:
            endpoint_parameter = WsRouteParameters(
                name=name,
                path=path,
                endpoint=endpoint_handler,
                encoding=encoding,
                use_extra_handler=use_extra_handler,
                extra_handler_type=extra_handler_type,
            )
            return self._get_ws_operation(ws_route_parameters=endpoint_parameter)

        return _decorator
