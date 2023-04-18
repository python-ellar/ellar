import inspect
import typing as t

from socketio import AsyncServer
from starlette.concurrency import run_in_threadpool
from starlette.routing import compile_path

from ellar.constants import (
    CONTROLLER_CLASS_KEY,
    EXTRA_ROUTE_ARGS_KEY,
    GUARDS_KEY,
    NOT_SET,
    SCOPE_SERVICE_PROVIDER,
)
from ellar.core import IExecutionContext
from ellar.core.context import IExecutionContextFactory
from ellar.core.exceptions import WebSocketRequestValidationError
from ellar.core.params import WebsocketEndpointArgsModel
from ellar.core.services import Reflector
from ellar.di import EllarInjector
from ellar.helper import get_name
from ellar.reflect import reflect
from ellar.socket_io.model import GatewayBase, GatewayContext
from ellar.socket_io.responses import WsResponse

if t.TYPE_CHECKING:
    from ellar.core import GuardCanActivate
    from ellar.core.params import ExtraEndpointArg


class SocketOperationConnection:
    __slots__ = (
        "_event",
        "_server",
        "endpoint",
        "_name",
        "_is_coroutine",
        "endpoint_parameter_model",
        "_control_type",
    )

    ws_endpoint_args_model: t.Type[
        WebsocketEndpointArgsModel
    ] = WebsocketEndpointArgsModel

    def __init__(
        self, event: str, server: AsyncServer, message_handler: t.Callable
    ) -> None:
        self._event = event
        self._server = server
        self.endpoint = message_handler
        self._name = get_name(self.endpoint)
        self._is_coroutine = inspect.iscoroutinefunction(message_handler)
        self.endpoint_parameter_model = NOT_SET
        self._load_model()
        self._register_handler()

    def _load_model(self) -> None:
        path_regex, path_format, param_convertors = compile_path("/")

        extra_route_args: t.Union[t.List["ExtraEndpointArg"], "ExtraEndpointArg"] = (
            reflect.get_metadata(EXTRA_ROUTE_ARGS_KEY, self.endpoint) or []
        )
        if not isinstance(extra_route_args, list):
            extra_route_args = [extra_route_args]

        if self.endpoint_parameter_model is NOT_SET:
            self.endpoint_parameter_model = self.ws_endpoint_args_model(
                path=path_format,
                endpoint=self.endpoint,
                param_converters=param_convertors,
                extra_endpoint_args=extra_route_args,
            )
            self.endpoint_parameter_model.build_model()

    async def _context_handler(self, sid: str, environment: t.Dict) -> t.Any:
        service_provider = t.cast(
            EllarInjector, environment["asgi.scope"][SCOPE_SERVICE_PROVIDER]
        )

        execution_context_factory = service_provider.get(IExecutionContextFactory)
        context = execution_context_factory.create_context(
            operation=self,
            scope=environment["asgi.scope"],
            receive=environment["asgi.receive"],
            send=environment["asgi.send"],
        )
        gateway_instance = self._get_gateway_instance_and_context(ctx=context, sid=sid)

        await self.run_route_guards(context=context)
        await self._run_handler(context=context, gateway_instance=gateway_instance)

    def _register_handler(self) -> None:
        @self._server.on(self._event)
        async def _handler(sid: str, *environment: t.Any) -> t.Any:
            sid_environ = self._server.get_environ(sid)
            await self._context_handler(
                sid, environment[0] if len(environment) == 1 else sid_environ
            )

    async def _run_handler(
        self, context: IExecutionContext, gateway_instance: GatewayBase
    ) -> t.Any:
        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )

        if gateway_instance.context.message:
            (
                _func_kwargs,
                _errors,
            ) = await self.endpoint_parameter_model.resolve_ws_body_dependencies(
                ctx=context, body_data=gateway_instance.context.message
            )

            func_kwargs.update(_func_kwargs)
            errors = errors + _errors

        if errors:
            raise WebSocketRequestValidationError(errors)
        if self._is_coroutine:
            res = await self.endpoint(gateway_instance, **func_kwargs)
        else:
            res = await run_in_threadpool(
                self.endpoint, gateway_instance, **func_kwargs
            )

        if res and isinstance(res, WsResponse):
            await self._server.emit(**res.dict())

    @t.no_type_check
    async def run_route_guards(self, context: IExecutionContext) -> None:
        reflector = context.get_service_provider().get(Reflector)
        app = context.get_app()

        targets = [self.endpoint, self.get_control_type()]

        _guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = reflector.get_all_and_override(GUARDS_KEY, *targets)

        if not _guards:
            _guards = app.get_guards()

        if _guards:
            for guard in _guards:
                if isinstance(guard, type):
                    guard = context.get_service_provider().get(guard)

                result = await guard.can_activate(context)
                if not result:
                    guard.raise_exception()

    def get_control_type(self) -> t.Type[GatewayBase]:
        """
        For operation under a controller, `get_control_type` and `get_class` will return the same result
        For operation under ModuleRouter, this will return a unique type created for the router for tracking some properties
        :return: a type that wraps the operation
        """
        if not hasattr(self, "_control_type"):
            _control_type = reflect.get_metadata(CONTROLLER_CLASS_KEY, self.endpoint)
            if _control_type is None:
                raise Exception("Operation must have a single control type.")
            self._control_type = t.cast(t.Type[GatewayBase], _control_type)

        return self._control_type

    def _get_gateway_instance(self, ctx: IExecutionContext) -> GatewayBase:
        gateway_type: t.Optional[t.Type] = reflect.get_metadata(
            CONTROLLER_CLASS_KEY, self.endpoint
        )
        if not gateway_type or (
            gateway_type and not issubclass(gateway_type, GatewayBase)
        ):
            raise RuntimeError("GatewayBase Type was not found")

        service_provider = ctx.get_service_provider()

        gateway_instance = service_provider.get(gateway_type)
        return t.cast(GatewayBase, gateway_instance)

    def _get_gateway_instance_and_context(
        self, ctx: IExecutionContext, sid: str, message: t.Any = None
    ) -> GatewayBase:
        sid_environ = self._server.get_environ(sid)
        gateway_instance = self._get_gateway_instance(ctx)
        gateway_instance.context = GatewayContext(
            server=self._server,
            context=ctx,
            sid=sid,
            environment=sid_environ,
            message=message,
        )
        return gateway_instance


class SocketMessageOperation(SocketOperationConnection):
    async def _context_handler(self, sid: str, message: t.Any) -> t.Any:
        sid_environ = self._server.get_environ(sid)
        if not sid_environ:
            raise Exception("Socket Environment not found.")

        service_provider = t.cast(
            EllarInjector, sid_environ["asgi.scope"][SCOPE_SERVICE_PROVIDER]
        )

        execution_context_factory = service_provider.get(IExecutionContextFactory)
        context = execution_context_factory.create_context(
            operation=self,
            scope=sid_environ["asgi.scope"],
            receive=sid_environ["asgi.receive"],
            send=sid_environ["asgi.send"],
        )

        gateway_instance = self._get_gateway_instance_and_context(
            ctx=context, sid=sid, message=message
        )

        await self.run_route_guards(context=context)
        await self._run_handler(context=context, gateway_instance=gateway_instance)

    def _register_handler(self) -> None:
        @self._server.on(self._event)
        async def _handler(sid: str, message: t.Any) -> t.Any:
            await self._context_handler(sid, message)
