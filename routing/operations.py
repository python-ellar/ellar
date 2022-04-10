import inspect
import typing as t
from abc import ABC, abstractmethod

from starlette.concurrency import run_in_threadpool
from starlette.routing import compile_path

from starletteapi.status import WS_1008_POLICY_VIOLATION

from starletteapi.constants import SCOPE_API_VERSIONING_RESOLVER, NOT_SET
from starletteapi.helper import generate_operation_unique_id
from starletteapi.operation_meta import OperationMeta
from starletteapi.types import ASGIApp, TScope, TReceive, TSend, T
from starletteapi.routing import StarletteRoute, WebSocketRoute, iscoroutinefunction_or_partial, Match
from starletteapi.context import ExecutionContext
from starletteapi.exceptions import RequestValidationError, WebSocketRequestValidationError, ImproperConfiguration
from starletteapi.guard import GuardInterface
from starletteapi.responses.model import RouteResponseModel
from starletteapi.route_models import APIEndpointParameterModel, WebsocketParameterModel
from starletteapi.controller.base import ControllerBase
from .websocket_handlers import WebSocketExtraHandler, ControllerWebSocketExtraHandler

if t.TYPE_CHECKING:
    from starletteapi.guard.base import GuardCanActivate
    from starletteapi.websockets import WebSocket
    from starletteapi.responses.model import ResponseModel

__all__ = [
    'WebsocketOperationBase',
    'ControllerWebsocketOperation',
    'ControllerOperation',
    'ClassBasedOperation',
    'WebsocketOperation',
    'Operation',
    'OperationBase',
    'ExtraOperationArg',
    'OperationMeta'
]


class RouteInvalidParameterException(Exception):
    pass


class ExtraOperationArg(t.Generic[T]):
    __slots__ = ('name', 'annotation', 'default')

    empty = inspect.Parameter.empty

    def __init__(self, *, name: str, annotation: t.Type[T], default_value: t.Any = None):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve(self, kwargs: t.Dict) -> T:
        if self.name in kwargs:
            return t.cast(t.Optional[T], kwargs.pop(self.name))
        raise AttributeError(f'{self.name} ExtraOperationArgs not found')


class OperationBase(GuardInterface):
    _meta: OperationMeta

    endpoint: t.Callable

    def __call__(self, *args, **kwargs):
        return self.endpoint(*args, **kwargs)

    @abstractmethod
    def _load_model(self):
        pass

    @property
    def app(self) -> ASGIApp:
        return self._run

    @app.setter
    def app(self, value):
        ...

    def get_guards(self) -> t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]:
        return list(self._meta.route_guards)

    def get_meta(self) -> OperationMeta:
        return self._meta

    def add_guards(self, *guards: t.Sequence['GuardCanActivate']) -> None:
        if guards:
            self._meta.route_guards += list(guards)

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

    async def _run(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        context = ExecutionContext.create_context(scope=scope, receive=receive, send=send, operation=self)
        await self.run_route_guards(context=context)
        await self._handle(context=context)

    @abstractmethod
    async def _handle(self, *, context: ExecutionContext) -> None:
        """return a context"""

    def get_allowed_version(self) -> t.Set[str]:
        return self._meta.route_versioning

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        match = super().matches(scope)
        if match[0] is not Match.NONE:
            version_scheme_resolver = t.cast('BaseAPIVersioningResolver', scope[SCOPE_API_VERSIONING_RESOLVER])
            if not version_scheme_resolver.can_activate(route_versions=self.get_allowed_version()):
                return Match.NONE, {}
        return match


class WebsocketOperationBase(OperationBase, ABC):
    pass


class Operation(OperationBase, StarletteRoute):
    __slots__ = (
        'endpoint', 'is_coroutine', 'route_parameter_model', '_meta',
        'route_parameter_model', 'response_model', 'defined_responses'
    )

    def __init__(
            self,
            *,
            path: str,
            methods: t.List[str],
            endpoint: t.Callable,
            operation_id: t.Optional[str] = None,
            summary: t.Optional[str] = None,
            description: t.Optional[str] = None,
            tags: t.Optional[t.List[str]] = None,
            deprecated: t.Optional[bool] = None,
            name: t.Optional[str] = None,
            include_in_schema: bool = True,
            response: t.Union[t.Dict[int, t.Union[t.Type, t.Any]], 'ResponseModel', None] = None,
    ) -> None:
        self.endpoint = endpoint
        self.is_coroutine = iscoroutinefunction_or_partial(self.endpoint)
        self.defined_responses = response

        super().__init__(
            path=path, endpoint=endpoint, methods=methods,
            name=name, include_in_schema=include_in_schema
        )
        self.route_parameter_model: APIEndpointParameterModel = NOT_SET
        self.response_model: RouteResponseModel = NOT_SET

        _meta = OperationMeta()
        if hasattr(self.endpoint, "_meta"):
            _meta = getattr(self.endpoint, "_meta")

        self._meta: OperationMeta = t.cast(OperationMeta, _meta)

        self._meta.update(
            operation_id=operation_id, summary=summary,
            description=description, deprecated=deprecated,
            tags=tags, operation_handler=self.endpoint
        )
        self._load_model()

    def _load_model(self):
        self.path_regex, self.path_format, self.param_convertors = compile_path(self.path)
        self.route_parameter_model = APIEndpointParameterModel(
            path=self.path_format, endpoint=self.endpoint,
            operation_unique_id=self.get_operation_unique_id(
                method=list(self.methods)[0]
            )
        )

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(*self._meta.extra_route_args)
        self.route_parameter_model.build_model()

        if self._meta.response_override:
            _response_override = self._meta.response_override
            if not isinstance(_response_override, dict):
                _response_override = {200: _response_override}
            self.defined_responses.update(_response_override)

        self.response_model = RouteResponseModel(
            route_responses=self.defined_responses
        )

    def get_operation_unique_id(self, method: str):
        return generate_operation_unique_id(
            name=self.name, path=self.path_format, method=method
        )

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            # TODO: raise Exception not RequestValidationError
            raise RequestValidationError(errors)
        if self.is_coroutine:
            response_obj = await self.endpoint(**func_kwargs)
        else:
            response_obj = await run_in_threadpool(self.endpoint, **func_kwargs)
        response = self.response_model.process_response(ctx=context, response_obj=response_obj)
        await response(context.scope, context.receive, context.send)

    def __hash__(self):
        return hash((self.path, tuple(self.methods)))


class WebsocketOperation(WebsocketOperationBase, WebSocketRoute):
    __slots__ = (
        'endpoint', '_handlers_kwargs', 'route_parameter_model', '_meta', '_extra_handler_type'
    )

    def __init__(
            self,
            *,
            path: str,
            name: t.Optional[str] = None,
            endpoint: t.Callable,
            encoding: str = 'json',
            use_extra_handler: bool = False,
            extra_handler_type: t.Optional[t.Type[WebSocketExtraHandler]] = None
    ) -> None:
        self.endpoint = endpoint
        self._handlers_kwargs: t.Dict[str, t.Optional[t.Callable]] = dict(
            on_receive=None, on_connect=None, on_disconnect=None, encoding=encoding
        )
        self._use_extra_handler = use_extra_handler
        self._extra_handler_type: t.Optional[WebSocketExtraHandler] = extra_handler_type

        super().__init__(
            path=path,
            endpoint=self.endpoint,
            name=name
        )
        self.route_parameter_model: WebsocketParameterModel = NOT_SET

        _meta = OperationMeta()
        if hasattr(self.endpoint, "_meta"):
            _meta = getattr(self.endpoint, "_meta")

        self._meta: OperationMeta = t.cast(OperationMeta, _meta)

        if self._use_extra_handler:
            self._handlers_kwargs.update(on_receive=self.endpoint)

        self._load_model()

    @classmethod
    def get_websocket_handler(cls) -> t.Type[WebSocketExtraHandler]:
        return WebSocketExtraHandler

    def connect(self, func: t.Callable[['WebSocket'], None]) -> t.Callable:
        self._handlers_kwargs.update(on_connect=func)
        return func

    def disconnect(self, func: t.Callable[['WebSocket', int], None]) -> t.Callable:
        self._handlers_kwargs.update(on_disconnect=func)
        return func

    def custom_handler(self, name) -> t.Callable:
        def _wrap(func: t.Callable) -> t.Callable:
            self._handlers_kwargs.update({name: func})
            return func

        return _wrap

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            websocket = context.switch_to_websocket()
            exc = WebSocketRequestValidationError(errors)
            await context.switch_to_websocket().send_json(
                dict(code=WS_1008_POLICY_VIOLATION, errors=exc.errors())
            )
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise exc

        if self._use_extra_handler:
            ws_extra_handler_type = self._extra_handler_type or self.get_websocket_handler()
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.route_parameter_model, **self._handlers_kwargs
            )
            await ws_extra_handler.dispatch(context=context, **func_kwargs)
        else:
            await self.endpoint(**func_kwargs)

    def _load_model(self):
        self.path_regex, self.path_format, self.param_convertors = compile_path(self.path)

        self.route_parameter_model = WebsocketParameterModel(
            path=self.path_format, endpoint=self.endpoint
        )

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(*self._meta.extra_route_args)
        self.route_parameter_model.build_model()

        if not self._use_extra_handler and self.route_parameter_model.body_resolver:
            raise ImproperConfiguration('`WsBody` should only be used when '
                                        '`use_extra_handler` flag is set to True in WsRoute')

    def __hash__(self):
        return hash((self.path, tuple(['ws'])))


class ClassBasedOperation:
    _meta: OperationMeta
    endpoint: t.Any

    def get_controller_class(self) -> t.Type[ControllerBase]:
        assert hasattr(self.endpoint, 'controller_class'), 'Controller Operation is not fully setup'
        return self.endpoint.controller_class

    def _get_controller_instance(self, ctx: ExecutionContext) -> ControllerBase:
        service_provider = ctx.get_service_provider()

        controller_instance = service_provider.get(
            self.get_controller_class()
        )
        controller_instance.context = ctx
        return controller_instance

    def __call__(self, context: ExecutionContext, *args, **kwargs):
        controller_instance = self._get_controller_instance(ctx=context)
        return self.endpoint(controller_instance, *args, **kwargs)


class ControllerOperation(ClassBasedOperation, Operation):
    async def _handle(self, context: ExecutionContext) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)

        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            raise RequestValidationError(errors)

        if self.is_coroutine:
            response_obj = await self.endpoint(controller_instance, **func_kwargs)
        else:
            response_obj = await run_in_threadpool(self.endpoint, controller_instance, **func_kwargs)
        response = self.response_model.process_response(ctx=context, response_obj=response_obj)
        await response(context.scope, context.receive, context.send)


class ControllerWebsocketOperation(ClassBasedOperation, WebsocketOperation):
    _extra_handler_type: t.Optional[ControllerWebSocketExtraHandler]

    @classmethod
    def get_websocket_handler(cls) -> t.Type[ControllerWebSocketExtraHandler]:
        return ControllerWebSocketExtraHandler

    async def _handle(self, context: ExecutionContext) -> None:
        controller_instance = self._get_controller_instance(ctx=context)
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            websocket = context.switch_to_websocket()
            exc = WebSocketRequestValidationError(errors)
            await context.switch_to_websocket().send_json(
                dict(code=WS_1008_POLICY_VIOLATION, errors=exc.errors())
            )
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise exc

        if self._use_extra_handler:
            ws_extra_handler_type = self._extra_handler_type or self.get_websocket_handler()
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.route_parameter_model,
                controller_instance=controller_instance, **self._handlers_kwargs,
            )
            await ws_extra_handler.dispatch(context=context, **func_kwargs)
        else:
            await self.endpoint(controller_instance, **func_kwargs)
