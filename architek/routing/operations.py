import inspect
import typing as t
from abc import ABC, abstractmethod

from starlette.concurrency import run_in_threadpool
from starlette.routing import (
    Match,
    Route as StarletteRoute,
    WebSocketRoute as StarletteWebSocketRoute,
    compile_path,
    iscoroutinefunction_or_partial,
)
from starlette.status import WS_1008_POLICY_VIOLATION

from architek.constants import NOT_SET, SCOPE_API_VERSIONING_RESOLVER
from architek.context import ExecutionContext
from architek.controller.base import ControllerBase
from architek.exceptions import (
    ImproperConfiguration,
    RequestValidationError,
    WebSocketRequestValidationError,
)
from architek.helper import generate_operation_unique_id, get_name
from architek.operation_meta import OperationMeta
from architek.response.model import RouteResponseModel
from architek.route_models import APIEndpointParameterModel, WebsocketParameterModel
from architek.types import T, TReceive, TScope, TSend

from .websocket_handlers import ControllerWebSocketExtraHandler, WebSocketExtraHandler

if t.TYPE_CHECKING:
    from architek.guard.base import GuardCanActivate
    from architek.response.model import ResponseModel
    from architek.versioning.resolver import BaseAPIVersioningResolver
    from architek.websockets import WebSocket

__all__ = [
    "WebsocketOperationBase",
    "ControllerWebsocketOperation",
    "ControllerOperation",
    "ClassBasedOperation",
    "WebsocketOperation",
    "Operation",
    "OperationBase",
    "ExtraOperationArg",
    "OperationMeta",
    "RouteOperationDecorator",
    "WebsocketOperationDecorator",
    "OperationDecorator",
]


class RouteInvalidParameterException(Exception):
    pass


class ExtraOperationArg(t.Generic[T]):
    __slots__ = ("name", "annotation", "default")

    empty = inspect.Parameter.empty

    def __init__(
        self, *, name: str, annotation: t.Type[T], default_value: t.Any = None
    ):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve(self, kwargs: t.Dict) -> T:
        if self.name in kwargs:
            return t.cast(T, kwargs.pop(self.name))
        raise AttributeError(f"{self.name} ExtraOperationArg not found")


class OperationBase:
    _meta: OperationMeta

    endpoint: t.Callable

    @t.no_type_check
    def __call__(
        self, context: ExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        return self.endpoint(*args, **kwargs)

    @abstractmethod
    def _load_model(self) -> None:
        pass

    def get_guards(
        self,
    ) -> t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]:
        return list(self._meta.route_guards)

    def get_meta(self) -> OperationMeta:
        return self._meta

    def update_operation_meta(self, **kwargs: t.Any) -> None:
        self._meta.update(**kwargs)

    async def run_route_guards(self, context: ExecutionContext) -> None:
        app = context.get_app()
        _guards = self.get_guards() or app.get_guards()
        if _guards:
            for guard in _guards:
                if isinstance(guard, type):
                    guard = guard()
                result = await guard.can_activate(context)
                if not result:
                    guard.raise_exception()

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        context = ExecutionContext.create_context(
            scope=scope, receive=receive, send=send, operation=self
        )
        await self.run_route_guards(context=context)
        await self._handle(context=context)

    @abstractmethod
    async def _handle(self, *, context: ExecutionContext) -> None:
        """return a context"""

    def get_allowed_version(self) -> t.Set[t.Union[int, float, str]]:
        return self._meta.route_versioning

    @classmethod
    def get_methods(cls, methods: t.Optional[t.List[str]] = None) -> t.Set[str]:
        if methods is None:
            methods = ["GET"]

        _methods = {method.upper() for method in methods}
        if "GET" in _methods:
            _methods.add("HEAD")

        return _methods

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        match = super().matches(scope)  # type: ignore
        if match[0] is not Match.NONE:
            version_scheme_resolver: "BaseAPIVersioningResolver" = t.cast(
                "BaseAPIVersioningResolver", scope[SCOPE_API_VERSIONING_RESOLVER]
            )
            if not version_scheme_resolver.can_activate(
                route_versions=self.get_allowed_version()
            ):
                return Match.NONE, {}
        return match  # type: ignore


class WebsocketOperationBase(OperationBase, ABC):
    pass


class Operation(OperationBase, StarletteRoute):
    methods: t.Set[str]

    __slots__ = (
        "endpoint",
        "_is_coroutine",
        "route_parameter_model",
        "_meta",
        "response_model",
        "_defined_responses",
    )

    def __init__(
        self,
        *,
        path: str,
        methods: t.List[str],
        endpoint: t.Callable,
        response: t.Union[t.Type, t.Dict[int, t.Type]],
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self._is_coroutine = iscoroutinefunction_or_partial(endpoint)
        self._defined_responses = response

        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = path
        self.endpoint = endpoint  # type: ignore

        self.name = get_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema
        self.methods = self.get_methods(methods)

        self.route_parameter_model: APIEndpointParameterModel = NOT_SET
        self.response_model: RouteResponseModel = NOT_SET
        _meta = getattr(self.endpoint, "_meta", {})
        self._meta: OperationMeta = OperationMeta(**_meta)

        self._meta.update(
            operation_handler=self.endpoint,
        )
        self._load_model()

    def _load_model(self) -> None:
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
        self.route_parameter_model = APIEndpointParameterModel(
            path=self.path_format,
            endpoint=self.endpoint,
            operation_unique_id=self.get_operation_unique_id(
                method=list(self.methods)[0]
            ),
        )

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(
                *self._meta.extra_route_args
            )
        self.route_parameter_model.build_model()

        if self._meta.response_override:
            _response_override = self._meta.response_override
            if not isinstance(_response_override, dict):
                _response_override = {200: _response_override}  # type: ignore
            self._defined_responses.update(_response_override)  # type: ignore

        self.response_model = RouteResponseModel(
            route_responses=self._defined_responses
        )

    def get_operation_unique_id(self, method: str) -> str:
        return generate_operation_unique_id(
            name=self.name, path=self.path_format, method=method
        )

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)
        if self._is_coroutine:
            response_obj = await self.endpoint(**func_kwargs)
        else:
            response_obj = await run_in_threadpool(self.endpoint, **func_kwargs)
        response = self.response_model.process_response(
            ctx=context, response_obj=response_obj
        )
        await response(context.scope, context.receive, context.send)

    def __hash__(self) -> int:
        return hash((self.path, tuple(self.methods)))


class WebSocketOperationMixin:
    _handlers_kwargs: t.Dict

    def connect(self, func: t.Callable[["WebSocket"], None]) -> t.Callable:
        self._handlers_kwargs.update(on_connect=func)
        return func

    def disconnect(self, func: t.Callable[["WebSocket", int], None]) -> t.Callable:
        self._handlers_kwargs.update(on_disconnect=func)
        return func

    def custom_handler(self, name: str) -> t.Callable:
        def _wrap(func: t.Callable) -> t.Callable:
            self._handlers_kwargs.update({name: func})
            return func

        return _wrap


class WebsocketOperation(
    WebsocketOperationBase, StarletteWebSocketRoute, WebSocketOperationMixin
):
    __slots__ = (
        "endpoint",
        "_handlers_kwargs",
        "route_parameter_model",
        "_meta",
        "_extra_handler_type",
    )

    def __init__(
        self,
        *,
        path: str,
        name: t.Optional[str] = None,
        endpoint: t.Callable,
        encoding: str = "json",
        use_extra_handler: bool = False,
        extra_handler_type: t.Optional[t.Type[WebSocketExtraHandler]] = None,
        **handlers_kwargs: t.Any,
    ) -> None:
        self._handlers_kwargs: t.Dict[str, t.Any] = dict(
            encoding=encoding,
            on_receive=None,
            on_connect=None,
            on_disconnect=None,
        )
        self._handlers_kwargs.update(handlers_kwargs)
        self._use_extra_handler = use_extra_handler
        self._extra_handler_type: t.Optional[
            t.Type[WebSocketExtraHandler]
        ] = extra_handler_type

        super().__init__(path=path, endpoint=endpoint, name=name)
        self.route_parameter_model: WebsocketParameterModel = NOT_SET

        _meta = getattr(self.endpoint, "_meta", {})
        self._meta: OperationMeta = OperationMeta(**_meta)

        if self._use_extra_handler:
            self._handlers_kwargs.update(on_receive=self.endpoint)
        self._load_model()

    @classmethod
    def get_websocket_handler(cls) -> t.Type[WebSocketExtraHandler]:
        return WebSocketExtraHandler

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            websocket = context.switch_to_websocket()
            exc = WebSocketRequestValidationError(errors)
            await context.switch_to_websocket().send_json(
                dict(code=WS_1008_POLICY_VIOLATION, errors=exc.errors())
            )
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise exc

        if self._use_extra_handler:
            ws_extra_handler_type = (
                self._extra_handler_type or self.get_websocket_handler()
            )
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.route_parameter_model,
                **self._handlers_kwargs,
            )
            await ws_extra_handler.dispatch(context=context, **func_kwargs)
        else:
            await self.endpoint(**func_kwargs)

    def _load_model(self) -> None:
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )

        self.route_parameter_model = WebsocketParameterModel(
            path=self.path_format, endpoint=self.endpoint
        )

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(
                *self._meta.extra_route_args
            )
        self.route_parameter_model.build_model()

        if not self._use_extra_handler and self.route_parameter_model.body_resolver:
            raise ImproperConfiguration(
                "`WsBody` should only be used when "
                "`use_extra_handler` flag is set to True in WsRoute"
            )

    def __hash__(self) -> int:
        return hash((self.path, tuple(["ws"])))


class ClassBasedOperation:
    _meta: OperationMeta
    endpoint: t.Callable

    def __init__(
        self, controller_type: t.Type[ControllerBase], *args: t.Any, **kwargs: t.Any
    ) -> None:
        super(ClassBasedOperation, self).__init__(*args, **kwargs)
        self.controller_type: t.Type[ControllerBase] = controller_type
        self._meta.update(controller_type=controller_type)

    def _get_controller_instance(self, ctx: ExecutionContext) -> ControllerBase:
        service_provider = ctx.get_service_provider()

        controller_instance = service_provider.get(self.controller_type)
        controller_instance.context = ctx
        return controller_instance

    @t.no_type_check
    def __call__(
        self, context: ExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)
        return self.endpoint(controller_instance, *args, **kwargs)


class ControllerOperation(ClassBasedOperation, Operation):
    async def _handle(self, context: ExecutionContext) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)

        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)

        if self._is_coroutine:
            response_obj = await self.endpoint(controller_instance, **func_kwargs)
        else:
            response_obj = await run_in_threadpool(
                self.endpoint, controller_instance, **func_kwargs
            )
        response = self.response_model.process_response(
            ctx=context, response_obj=response_obj
        )
        await response(context.scope, context.receive, context.send)


class ControllerWebsocketOperation(ClassBasedOperation, WebsocketOperation):
    _extra_handler_type: t.Optional[t.Type[ControllerWebSocketExtraHandler]]

    @classmethod
    def get_websocket_handler(cls) -> t.Type[ControllerWebSocketExtraHandler]:
        return ControllerWebSocketExtraHandler

    async def _handle(self, context: ExecutionContext) -> None:
        controller_instance = self._get_controller_instance(ctx=context)
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            websocket = context.switch_to_websocket()
            exc = WebSocketRequestValidationError(errors)
            await context.switch_to_websocket().send_json(
                dict(code=WS_1008_POLICY_VIOLATION, errors=exc.errors())
            )
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise exc

        if self._use_extra_handler:
            ws_extra_handler_type = (
                self._extra_handler_type or self.get_websocket_handler()
            )
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.route_parameter_model,
                controller_instance=controller_instance,
                **self._handlers_kwargs,
            )
            await ws_extra_handler.dispatch(context=context, **func_kwargs)
        else:
            await self.endpoint(controller_instance, **func_kwargs)


class OperationDecorator:
    def create_operation(
        self, controller_type: t.Type[ControllerBase]
    ) -> t.Union[ControllerOperation, ControllerWebsocketOperation]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}, path: {self.__str__()}>"


class RouteOperationDecorator(OperationDecorator):
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
        self.operation: t.Optional[ControllerOperation] = None

    def create_operation(
        self, controller_type: t.Type[ControllerBase]
    ) -> ControllerOperation:
        if not self.operation:
            self.operation = ControllerOperation(
                **self._init_kwargs, controller_type=controller_type
            )
        return self.operation

    def __str__(self) -> str:
        return self.path


class WebsocketOperationDecorator(OperationDecorator, WebSocketOperationMixin):
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
        self.operation: t.Optional[ControllerWebsocketOperation] = None

    def create_operation(
        self, controller_type: t.Type[ControllerBase]
    ) -> ControllerWebsocketOperation:
        if not self.operation:
            kwargs = dict(self._init_kwargs)
            kwargs.update(**self._handlers_kwargs)
            self.operation = ControllerWebsocketOperation(
                **kwargs,
                controller_type=controller_type,
            )
        return self.operation

    def __str__(self) -> str:
        return self.path
