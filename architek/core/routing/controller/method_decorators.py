import typing as t

from ..websocket import WebSocketExtraHandler, WebSocketOperationMixin
from .model import ControllerBase
from .route import ControllerRouteOperation
from .websocket import ControllerWebsocketRouteOperation

if t.TYPE_CHECKING:
    from architek.core.response.model import ResponseModel

__all__ = [
    "RouteMethodDecoratorBase",
    "RouteMethodDecorator",
    "WebsocketMethodDecorator",
]


class RouteMethodDecoratorBase:
    def create_operation(
        self, controller_type: t.Type[ControllerBase]
    ) -> t.Union[ControllerRouteOperation, ControllerWebsocketRouteOperation]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}, path: {self.__str__()}>"


class RouteMethodDecorator(RouteMethodDecoratorBase):
    def __init__(
        self,
        path: str,
        methods: t.List[str],
        endpoint: t.Callable,
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        response: t.Union[
            t.Dict[int, t.Union[t.Type, t.Any]], "ResponseModel", None
        ] = None,
    ):
        self.path = path
        self._init_kwargs = dict(
            path=path,
            methods=methods,
            endpoint=endpoint,
            name=name,
            include_in_schema=include_in_schema,
            response=response,
        )
        self.operation: t.Optional[ControllerRouteOperation] = None

    def create_operation(
        self, controller_type: t.Type["ControllerBase"]
    ) -> ControllerRouteOperation:
        if not self.operation:
            self.operation = ControllerRouteOperation(
                **self._init_kwargs, controller_type=controller_type
            )
        return self.operation

    def __str__(self) -> str:
        return self.path


class WebsocketMethodDecorator(RouteMethodDecoratorBase, WebSocketOperationMixin):
    def __init__(
        self,
        *,
        path: str,
        name: t.Optional[str] = None,
        endpoint: t.Callable,
        encoding: str = "json",
        use_extra_handler: bool = False,
        extra_handler_type: t.Optional[t.Type[WebSocketExtraHandler]] = None,
    ):
        self.path = path
        self._init_kwargs = dict(
            path=path,
            extra_handler_type=extra_handler_type,
            endpoint=endpoint,
            name=name,
            use_extra_handler=use_extra_handler,
            encoding=encoding,
        )
        self._handlers_kwargs: t.Dict[str, t.Any] = dict(
            on_receive=None, on_connect=None, on_disconnect=None, encoding=encoding
        )
        self.operation: t.Optional[ControllerWebsocketRouteOperation] = None

    def create_operation(
        self, controller_type: t.Type["ControllerBase"]
    ) -> ControllerWebsocketRouteOperation:
        if not self.operation:
            kwargs = dict(self._init_kwargs)
            kwargs.update(**self._handlers_kwargs)
            self.operation = ControllerWebsocketRouteOperation(
                **kwargs,
                controller_type=controller_type,
            )
        return self.operation

    def __str__(self) -> str:
        return self.path
