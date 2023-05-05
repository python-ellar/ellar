import typing as t

from ellar.common.constants import CONTROLLER_CLASS_KEY
from ellar.common.interfaces import IExecutionContext
from ellar.common.models import ControllerBase
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.services.reflector import Reflector

from .host import HostContext


class ExecutionContext(HostContext, IExecutionContext):
    """
    Context for route functions and controllers
    """

    __slots__ = ("_operation_handler", "reflector", "_handler_controller_class")

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
        _handler_controller_class = self.reflector.get(
            CONTROLLER_CLASS_KEY, self.get_handler()
        )

        self._handler_controller_class: t.Optional[t.Type["ControllerBase"]] = t.cast(
            t.Optional[t.Type["ControllerBase"]], _handler_controller_class
        )

    def get_handler(self) -> t.Callable:
        assert self._operation_handler, "Operation is not available yet."
        return self._operation_handler

    def get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        return self._handler_controller_class
