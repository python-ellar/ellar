import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Any, Dict, Sequence, Union, Type, cast, Generic, TypeVar, Set, Tuple

from starlette.concurrency import run_in_threadpool
from starlette.status import WS_1008_POLICY_VIOLATION

from starletteapi.constants import SCOPE_API_VERSIONING_RESOLVER
from starletteapi.helper import generate_operation_unique_id
from starletteapi.operation_meta import OperationMeta
from starletteapi.types import ASGIApp, TScope, TReceive, TSend
from starletteapi.routing import Route, WebSocketRoute, iscoroutinefunction_or_partial, Match
from starletteapi.context import ExecutionContext
from starletteapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from starletteapi.guard import GuardInterface
from starletteapi.responses.model import RouteResponseModel
from starletteapi.route_models import EndpointParameterModel, APIEndpointParameterModel
from starletteapi.schema import RouteParameters, WsRouteParameters
from starletteapi.controller.base import Controller, ControllerBase

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
    __slots__ = ('name', 'annotation', 'default')

    empty = inspect.Parameter.empty

    def __init__(self, *, name: str, annotation: Type[T], default_value: Any = None):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve_args(self, kwargs: Dict) -> T:
        if self.name in kwargs:
            return cast(Optional[T], kwargs.pop(self.name))
        raise AttributeError(f'{self.name} ExtraOperationArgs not found')


class OperationBase(GuardInterface):
    _meta: OperationMeta

    @property
    def app(self) -> ASGIApp:
        return self._run

    @app.setter
    def app(self, value):
        ...

    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        return list(self._meta.route_guards)

    def get_meta(self) -> Dict[str, Any]:
        return self._meta

    def add_guards(self, *guards: Sequence['GuardCanActivate']) -> None:
        if guards:
            self._meta.route_guards += list(guards)

    def update_operation_meta(self, **kwargs: Any) -> None:
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

    def get_allowed_version(self) -> Set[str]:
        return self._meta.route_versioning

    def matches(self, scope: TScope) -> Tuple[Match, TScope]:
        match = super().matches(scope)
        if match[0] is not Match.NONE:
            version_scheme_resolver = cast('BaseAPIVersioningResolver', scope[SCOPE_API_VERSIONING_RESOLVER])
            if not version_scheme_resolver.can_activate(route_versions=self.get_allowed_version()):
                return Match.NONE, {}
        return match


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

        self.route_parameter_model = APIEndpointParameterModel(
            path=self.path_format, endpoint=self.endpoint,
            operation_unique_id=self.get_operation_unique_id(
                method=list(self.methods)[0]
            )
        )
        _meta = OperationMeta()
        if hasattr(self.endpoint, "_meta"):
            _meta = getattr(self.endpoint, "_meta")

        self._meta: OperationMeta = cast(OperationMeta, _meta)

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(*self._meta.extra_route_args)

        self.response_model = RouteResponseModel(
            route_responses=self._meta.response_override or route_parameter.response
        )
        self._meta.update(
            operation_id=route_parameter.operation_id, summary=route_parameter.summary,
            description=route_parameter.description, deprecated=route_parameter.deprecated,
            tags=route_parameter.tags
        )

    def get_operation_unique_id(self, method: str):
        return generate_operation_unique_id(
            name=self.name, path=self.path_format, method=method
        )

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
        self.route_parameter_model = EndpointParameterModel(
            path=self.path_format, endpoint=self.endpoint
        )
        _meta = OperationMeta()
        if hasattr(self.endpoint, "_meta"):
            _meta = getattr(self.endpoint, "_meta")

        self._meta: OperationMeta = cast(OperationMeta, _meta)

        if self._meta.extra_route_args:
            self.route_parameter_model.add_extra_route_args(*self._meta.extra_route_args)

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            websocket = context.switch_to_websocket()
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise WebSocketRequestValidationError(errors)

        await self.endpoint(**func_kwargs)


class ClassBasedOperation:
    _meta: OperationMeta

    def __init__(
            self, *, controller: Optional[Controller] = None, **kwargs: Any
    ) -> None:
        super(ClassBasedOperation, self).__init__(**kwargs)
        self._controller: Optional[Controller] = controller

    @property
    def controller(self) -> Controller:
        assert self._controller, 'Controller Operation is not fully setup'
        return self._controller

    @controller.setter
    def controller(self, value: Controller):
        if not isinstance(value, Controller):
            raise Exception('value must be instance of a Controller')
        self._controller = value

    def _get_controller_instance(self, ctx: ExecutionContext) -> ControllerBase:
        service_provider = ctx.get_service_provider()

        controller_instance = service_provider.get(
            self.controller.controller_class
        )
        controller_instance.context = ctx
        return controller_instance

    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        return self._meta.route_guards or self.controller.get_guards()

    def get_allowed_version(self) -> Set[str]:
        return self._meta.route_versioning or self.controller.version


class ControllerOperation(ClassBasedOperation, Operation):
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
    async def _handle(self, context: ExecutionContext) -> None:
        controller_instance = self._get_controller_instance(ctx=context)
        context.get_service_provider().update_context(ControllerBase, controller_instance)

        func_kwargs, errors = await self.route_parameter_model.resolve_dependencies(ctx=context)
        if errors:
            websocket = context.switch_to_websocket()
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise WebSocketRequestValidationError(errors)

        await self.endpoint(controller_instance, **func_kwargs)
