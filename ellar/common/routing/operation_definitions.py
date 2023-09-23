import functools
import typing as t
from functools import partial
from types import FunctionType

from ellar.common.constants import (
    DELETE,
    GET,
    HEAD,
    OPERATION_ENDPOINT_KEY,
    OPTIONS,
    PATCH,
    POST,
    PUT,
    ROUTE_OPERATION_PARAMETERS,
    TRACE,
)

from .schema import RouteParameters, WsRouteParameters


def _websocket_connection_attributes(func: t.Callable) -> t.Callable:
    def _advance_function(
        websocket_handler: t.Callable, handler_name: str
    ) -> t.Callable:
        def _wrap(connect_handler: t.Callable) -> t.Callable:
            if not (
                callable(websocket_handler) and type(websocket_handler) == FunctionType
            ):
                raise Exception(
                    "Invalid type. Please make sure you passed the websocket handler."
                )

            _item: t.Optional[WsRouteParameters] = getattr(
                websocket_handler, ROUTE_OPERATION_PARAMETERS, None
            )

            if not _item or not isinstance(_item, WsRouteParameters):
                raise Exception(
                    "Invalid type. Please make sure you passed the websocket handler."
                )

            _item.add_websocket_handler(
                handler_name=handler_name, handler=connect_handler
            )

            return connect_handler

        return _wrap

    func.connect = functools.partial(_advance_function, handler_name="on_connect")  # type: ignore[attr-defined]
    func.disconnect = functools.partial(_advance_function, handler_name="on_disconnect")  # type: ignore[attr-defined]
    return func


class OperationDefinitions:
    __slots__ = ()

    def _get_operation(self, route_parameter: RouteParameters) -> t.Callable:
        setattr(route_parameter.endpoint, OPERATION_ENDPOINT_KEY, True)
        setattr(route_parameter.endpoint, ROUTE_OPERATION_PARAMETERS, route_parameter)
        return route_parameter.endpoint

    def _get_ws_operation(self, ws_route_parameters: WsRouteParameters) -> t.Callable:
        setattr(ws_route_parameters.endpoint, OPERATION_ENDPOINT_KEY, True)
        setattr(
            ws_route_parameters.endpoint,
            ROUTE_OPERATION_PARAMETERS,
            ws_route_parameters,
        )
        return ws_route_parameters.endpoint

    def _get_decorator_or_operation(
        self, path: t.Union[str, t.Callable], endpoint_parameter_partial: t.Callable
    ) -> t.Callable:
        if callable(path):
            route_parameter = endpoint_parameter_partial(endpoint=path, path="/")
            self._get_operation(route_parameter=route_parameter)
            return path

        def _decorator(endpoint_handler: t.Callable) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
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
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Type], t.List[t.Tuple[int, t.Type]], t.Type, t.Any
        ] = None,
    ) -> t.Callable:
        def _decorator(endpoint_handler: t.Callable) -> t.Callable:
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

    @_websocket_connection_attributes
    def ws_route(
        self,
        path: str = "/",
        *,
        name: t.Optional[str] = None,
        encoding: t.Optional[str] = "json",
        use_extra_handler: bool = False,
        extra_handler_type: t.Optional[t.Type] = None,
    ) -> t.Callable:
        def _decorator(
            endpoint_handler: t.Callable,
        ) -> t.Callable:
            endpoint_parameter = WsRouteParameters(
                name=name,
                path=path,
                endpoint=endpoint_handler,
                encoding=encoding,
                use_extra_handler=use_extra_handler,
                extra_handler_type=extra_handler_type,
            )
            self._get_ws_operation(ws_route_parameters=endpoint_parameter)
            return endpoint_handler

        return _decorator
