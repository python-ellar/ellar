import typing as t

from ellar.common import (
    Identity,
    IExecutionContext,
    IHTTPHostContext,
    IWebSocketHostContext,
)
from ellar.common.types import TReceive, TScope, TSend
from ellar.di import EllarInjector
from socketio import AsyncServer

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app import App

    from .model import GatewayBase


class GatewayContext(IExecutionContext):
    def __init__(
        self,
        server: AsyncServer,
        sid: str,
        message: t.Any,
        context: "IExecutionContext",
        environment: t.Dict,
    ) -> None:
        self.server = server
        self.sid = sid
        self.message = message
        self._context = context
        self.environment = environment

    def get_handler(self) -> t.Callable:
        return self._context.get_handler()

    def get_class(self) -> t.Optional[t.Type["GatewayBase"]]:  # type: ignore[override]
        return t.cast(t.Type["GatewayBase"], self._context.get_class())

    def get_service_provider(self) -> EllarInjector:  # pragma: no cover
        return self._context.get_service_provider()

    def switch_to_http_connection(self) -> IHTTPHostContext:  # pragma: no cover
        return self._context.switch_to_http_connection()

    def switch_to_websocket(self) -> IWebSocketHostContext:  # pragma: no cover
        return self._context.switch_to_websocket()

    def get_app(self) -> "App":  # pragma: no cover
        return self._context.get_app()

    def get_type(self) -> str:  # pragma: no cover
        return self._context.get_type()

    def get_args(self) -> t.Tuple[TScope, TReceive, TSend]:  # pragma: no cover
        return self._context.get_args()

    @property
    def user(self) -> Identity:  # pragma: no cover
        return self._context.user

    @user.setter
    def user(self, value: Identity) -> None:  # pragma: no cover
        self._context.user = value
