import typing as t

from ellar.constants import CONTROLLER_CLASS_KEY, SCOPE_SERVICE_PROVIDER
from ellar.services.reflector import Reflector
from ellar.types import TReceive, TScope, TSend

from .exceptions import ExecutionContextException
from .host import HostContext
from .interface import IExecutionContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.controller import ControllerBase
    from ellar.core.routing import RouteOperationBase
    from ellar.di.injector import RequestServiceProvider


class ExecutionContext(HostContext, IExecutionContext):
    __slots__ = ("_operation_handler",)

    def __init__(
        self,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
        operation_handler: t.Callable = None,
    ) -> None:
        super(ExecutionContext, self).__init__(scope=scope, receive=receive, send=send)
        self._operation_handler = operation_handler

    def set_operation(self, operation: t.Optional["RouteOperationBase"] = None) -> None:
        if operation:
            self._operation_handler = operation.endpoint

    def get_handler(self) -> t.Callable:
        assert self._operation_handler, "Operation is not available yet."
        return self._operation_handler

    def get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        reflector = self.get_service_provider().get(Reflector)
        result: t.Optional[t.Type["ControllerBase"]] = reflector.get(
            CONTROLLER_CLASS_KEY, self.get_handler()
        )
        return result

    @classmethod
    def create_context(
        cls,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
        operation: t.Optional["RouteOperationBase"] = None,
    ) -> "ExecutionContext":
        execution_context = cls(
            scope=scope,
            receive=receive,
            send=send,
            operation_handler=operation.endpoint if operation else None,
        )
        request_provider: "RequestServiceProvider" = t.cast(
            "RequestServiceProvider", scope.get(SCOPE_SERVICE_PROVIDER)
        )
        if not request_provider:
            raise ExecutionContextException(
                "RequestServiceProvider is not configured. "
                "Please ensure `RequestServiceProviderMiddleware` is registered."
            )

        request_provider.update_context(
            t.cast(t.Type, IExecutionContext), execution_context
        )
        request_provider.update_context(cls, execution_context)
        return execution_context
