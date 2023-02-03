import typing as t
from functools import partial

from ellar.constants import (
    DELETE,
    GET,
    HEAD,
    OPERATION_ENDPOINT_KEY,
    OPTIONS,
    PATCH,
    POST,
    PUT,
    TRACE,
)
from ellar.core.schema import RouteParameters, WsRouteParameters
from ellar.helper import class_base_function_regex
from ellar.types import TCallable

from .controller.route import ControllerRouteOperation
from .controller.websocket.route import ControllerWebsocketRouteOperation
from .route import RouteOperation
from .websocket import WebsocketRouteOperation

TOperation = t.Union[RouteOperation, ControllerRouteOperation]
TWebsocketOperation = t.Union[
    WebsocketRouteOperation, ControllerWebsocketRouteOperation
]


class OperationDefinitions:
    __slots__ = ()

    def _get_http_operations_class(self, func: t.Callable) -> t.Type[TOperation]:
        if class_base_function_regex.match(repr(func)):
            return ControllerRouteOperation
        return RouteOperation

    def _get_ws_operations_class(self, func: t.Callable) -> t.Type[TWebsocketOperation]:
        if class_base_function_regex.match(repr(func)):
            return ControllerWebsocketRouteOperation
        return WebsocketRouteOperation

    def _get_operation(self, route_parameter: RouteParameters) -> TOperation:
        _operation_class = self._get_http_operations_class(route_parameter.endpoint)
        _operation = _operation_class(**route_parameter.dict())
        setattr(route_parameter.endpoint, OPERATION_ENDPOINT_KEY, True)
        return _operation

    def _get_ws_operation(
        self, ws_route_parameters: WsRouteParameters
    ) -> TWebsocketOperation:
        _ws_operation_class = self._get_ws_operations_class(
            ws_route_parameters.endpoint
        )
        _operation = _ws_operation_class(**ws_route_parameters.dict())
        setattr(ws_route_parameters.endpoint, OPERATION_ENDPOINT_KEY, True)
        return _operation

    def _get_decorator_or_operation(
        self, path: t.Union[str, t.Callable], endpoint_parameter_partial: t.Callable
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        if callable(path):
            route_parameter = endpoint_parameter_partial(endpoint=path, path="/")
            self._get_operation(route_parameter=route_parameter)
            return path

        def _decorator(endpoint_handler: TCallable) -> TCallable:
            _route_parameter = endpoint_parameter_partial(
                endpoint=endpoint_handler, path=path
            )
            self._get_operation(route_parameter=_route_parameter)
            return endpoint_handler

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
        path: str = "/",
        *,
        methods: t.List[str],
        name: str = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, None
        ] = None,
    ) -> t.Callable[[TCallable], t.Union[TOperation, TCallable]]:
        def _decorator(endpoint_handler: TCallable) -> TCallable:
            endpoint_parameter = RouteParameters(
                name=name,
                path=path,
                methods=methods,
                include_in_schema=include_in_schema,
                response=response,
                endpoint=endpoint_handler,
            )
            self._get_operation(route_parameter=endpoint_parameter)
            return endpoint_handler

        return _decorator

    def ws_route(
        self,
        path: str = "/",
        *,
        name: str = None,
        encoding: t.Optional[str] = "json",
        use_extra_handler: bool = False,
        extra_handler_type: t.Optional[t.Type] = None,
    ) -> t.Callable[[TCallable], t.Union[TCallable, TWebsocketOperation]]:
        def _decorator(
            endpoint_handler: TCallable,
        ) -> t.Union[TCallable, TWebsocketOperation]:
            endpoint_parameter = WsRouteParameters(
                name=name,
                path=path,
                endpoint=endpoint_handler,
                encoding=encoding,
                use_extra_handler=use_extra_handler,
                extra_handler_type=extra_handler_type,
            )
            operation = self._get_ws_operation(ws_route_parameters=endpoint_parameter)
            if use_extra_handler:
                return operation
            return endpoint_handler

        return _decorator
