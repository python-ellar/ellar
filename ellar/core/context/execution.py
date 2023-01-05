import typing as t

from ellar.compatible import cached_property
from ellar.constants import CONTROLLER_CLASS_KEY, SCOPE_SERVICE_PROVIDER
from ellar.di import injectable
from ellar.di.providers import ModuleProvider
from ellar.services.reflector import Reflector
from ellar.types import TReceive, TScope, TSend

from .exceptions import ExecutionContextException
from .host import HostContext
from .interface import IExecutionContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.controller import ControllerBase
    from ellar.core.routing import RouteOperationBase
    from ellar.di.injector import RequestServiceProvider


@injectable()
class ExecutionContext(HostContext, IExecutionContext):
    """
    Context for route functions and controllers
    """

    __slots__ = ("_operation_handler",)

    def __init__(
        self,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
        operation_handler: t.Callable,
        reflector: Reflector,
    ) -> None:
        super(ExecutionContext, self).__init__(scope=scope, receive=receive, send=send)
        self._operation_handler = operation_handler
        self.reflector = reflector

    def get_handler(self) -> t.Callable:
        assert self._operation_handler, "Operation is not available yet."
        return self._operation_handler

    @cached_property
    def _get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        result = self.reflector.get(CONTROLLER_CLASS_KEY, self.get_handler())
        return t.cast(t.Optional[t.Type["ControllerBase"]], result)

    def get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        return self._get_class  # type: ignore

    @classmethod
    def create_context(
        cls,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
        operation: "RouteOperationBase",
    ) -> IExecutionContext:
        provider = ModuleProvider(
            cls,
            scope=scope,
            receive=receive,
            send=send,
            operation_handler=operation.endpoint,
        )
        request_provider: "RequestServiceProvider" = t.cast(
            "RequestServiceProvider", scope.get(SCOPE_SERVICE_PROVIDER)
        )
        if not request_provider:
            raise ExecutionContextException(
                "RequestServiceProvider is not configured. "
                "Please ensure `RequestServiceProviderMiddleware` is registered."
            )

        request_provider.update_context(IExecutionContext, provider)
        execution_context = request_provider.get(IExecutionContext)  # type: ignore

        return execution_context
