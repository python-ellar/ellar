import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Any, Dict, Sequence, Union, Type, cast, Generic, TypeVar

from starlette.concurrency import run_in_threadpool
from starlette.routing import iscoroutinefunction_or_partial
from starlette.status import WS_1008_POLICY_VIOLATION
from starletteapi.types import ASGIApp, TScope, TReceive, TSend
from starletteapi.routing import Route, WebSocketRoute
from starletteapi.context import ExecutionContext
from starletteapi.api_documentation import OpenAPIDocumentation
from starletteapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from starletteapi.guard import GuardInterface
from starletteapi.responses.model import RouteResponseModel
from starletteapi.routing.route_models.route_param_model import RouteParameterModel
from starletteapi.schema import RouteParameters, WsRouteParameters
from starletteapi.controller.base import ControllerBase

if TYPE_CHECKING:
    from starletteapi.guard.base import GuardCanActivate

T = TypeVar('T')

__all__ = [
    'WebsocketOperationBase',
    'ControllerWebsocketOperation',
    'ControllerOperation',
    'ClassBasedOperation',
    'WebsocketOperation',
    'Operation',
    'OperationBase',
    'ExtraOperationArgs',
    'OperationMeta'
]


class RouteInvalidParameterException(Exception):
    pass


class ExtraOperationArgs(Generic[T]):
    empty = inspect.Parameter.empty

    def __init__(self, *, name: str, annotation: Type[T], default_value: Any = None):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve_args(self, kwargs: Dict) -> T:
        if self.name in kwargs:
            return cast(Optional[T], kwargs.pop(self.name))
        raise AttributeError(f'{self.name} ExtraOperationArgs not found')


class OperationMeta(dict):
    extra_route_args: List[ExtraOperationArgs]
    response_override: Union[Dict[int, Union[Type, Any]], Type, None]

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault('extra_route_args', [])
        kwargs.setdefault('response_override')
        super(OperationMeta, self).__init__(**kwargs)

    def __getattr__(self, name) -> Any:
        if name in self:
            value = self.get(name)
            return value
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class OperationBase(GuardInterface):
    _guards: List[Union[Type['GuardCanActivate'], 'GuardCanActivate']] = []
    _meta: Dict[str, Any] = {}

    @property
    def app(self) -> ASGIApp:
        return self._run

    @app.setter
    def app(self, value):
        ...

    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        return self._guards

    def get_meta(self) -> Dict[str, Any]:
        return self._meta

    def add_guards(self, *guards: Sequence['GuardCanActivate']) -> None:
        if guards:
            self._guards += list(guards)

    def update_operation_meta(self, **kwargs: Any) -> None:
        self._meta.update(**kwargs)

    async def run_route_guards(self, context: ExecutionContext) -> None:
        app = context.get_app()
        _guards = self.get_guards() or app.get_guards()
        if self._guards:
            injector = context.get_service_provider()
            for guard in self._guards:
                if isinstance(guard, type):
                    guard = injector.get(cast(Type['GuardCanActivate'], guard))
                result = await guard.can_activate(context)
                if not result:
                    guard.raise_exception()

    async def _run(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        context = ExecutionContext(scope=scope, receive=receive, send=send, operation=self)
        await self.run_route_guards(context=context)
        await self._handle(context=context)

    @abstractmethod
    async def _handle(self, *, context: ExecutionContext) -> None:
        """return a context"""


class WebsocketOperationBase(OperationBase, ABC):
    pass


class Operation(OperationBase, Route):
    def __init__(
            self,
            *,
            route_parameter: RouteParameters
    ) -> None:
        self.endpoint = route_parameter.endpoint
        self.is_coroutine = iscoroutinefunction_or_partial(self.endpoint)

        super().__init__(
            path=route_parameter.path, endpoint=route_parameter.endpoint, methods=route_parameter.methods,
            name=route_parameter.name, include_in_schema=route_parameter.include_in_schema
        )
        self.route_parameter_model = RouteParameterModel(path=self.path_format, endpoint=self.endpoint)
        _meta = OperationMeta()
        if hasattr(self.endpoint, "_meta"):
            _meta = getattr(self.endpoint, "_meta")

        self._meta: OperationMeta = cast(OperationMeta, _meta)

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(*self._meta.extra_route_args)

        self._guards: List[Union[Type['GuardCanActivate'], 'GuardCanActivate']] = []
        self.response_model = RouteResponseModel(
            route_responses=self._meta.response_override or route_parameter.response
        )
        self.open_api_documentation = OpenAPIDocumentation(
            operation_id=route_parameter.operation_id, summary=route_parameter.summary,
            description=route_parameter.description, deprecated=route_parameter.deprecated,
            tags=route_parameter.tags, route_parameter_model=self.route_parameter_model
        )
        _guards = getattr(self.endpoint, '_guards', [])
        if _guards:
            self.add_guards(*_guards)

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            raise RequestValidationError(errors)
        if self.is_coroutine:
            response_obj = await self.endpoint(**func_kwargs)
        else:
            response_obj = await run_in_threadpool(self.endpoint, **func_kwargs)
        response = self.response_model.process_response(ctx=context, response_obj=response_obj)
        await response(context.scope, context.receive, context.send)


class WebsocketOperation(WebsocketOperationBase, WebSocketRoute):
    def __init__(self, *, ws_route_parameters: WsRouteParameters) -> None:
        self.endpoint = ws_route_parameters.endpoint
        self.is_coroutine = iscoroutinefunction_or_partial(self.endpoint)

        super().__init__(
            path=ws_route_parameters.path,
            endpoint=self.endpoint,
            name=ws_route_parameters.name
        )

        self.route_parameter_model = RouteParameterModel(path=self.path_format, endpoint=self.endpoint)

        self._meta: Dict[str, Any] = {}
        self._guards: List[Union[Type['GuardCanActivate'], 'GuardCanActivate']] = []

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            websocket = context.switch_to_websocket()
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise WebSocketRequestValidationError(errors)

        await self.endpoint(**func_kwargs)


class ClassBasedOperation:
    def __init__(
            self, *, controller_class: Optional[ControllerBase] = None, **kwargs: Any
    ) -> None:
        super(ClassBasedOperation, self).__init__(**kwargs)
        self._controller_class: Optional[Type[ControllerBase]] = controller_class

    @property
    def controller_class(self) -> Type[ControllerBase]:
        assert self._controller_class, 'Controller Operation is not fully setup'
        return self._controller_class

    @controller_class.setter
    def controller_class(self, value: Type[ControllerBase]):
        if not isinstance(value, type):
            raise Exception('Value must be a type')
        self._controller_class = value

    def _get_controller_instance(self, ctx: ExecutionContext) -> ControllerBase:
        service_provider = ctx.get_service_provider()

        controller_instance = service_provider.get(
            self.controller_class
        )
        controller_instance.context = ctx
        return controller_instance


class ControllerOperation(ClassBasedOperation, Operation):

    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        return self._guards or self.controller_class.get_guards()

    async def _handle(self, context: ExecutionContext) -> Any:
        controller_instance = self._get_controller_instance(ctx=context)
        context.get_service_provider().update_context(ControllerBase, controller_instance)

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
    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        return self._guards or self.controller_class.get_guards()

    async def _handle(self, context: ExecutionContext) -> None:
        controller_instance = self._get_controller_instance(ctx=context)
        context.get_service_provider().update_context(ControllerBase, controller_instance)

        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            websocket = context.switch_to_websocket()
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise WebSocketRequestValidationError(errors)

        await self.endpoint(controller_instance, **func_kwargs)
