import typing as t

from ellar.common import (
    Identity,
    IHTTPConnectionContextFactory,
    IHTTPHostContext,
    IWebSocketContextFactory,
    IWebSocketHostContext,
)
from ellar.common.compatible import cached_property
from ellar.common.interfaces import IHostContext
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.execution_context.injector import current_injector

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app.main import App
    from ellar.di import EllarInjector


class HostContext(IHostContext):
    __slots__ = (
        "scope",
        "receive",
        "send",
    )

    def __init__(
        self,
        *,
        scope: TScope,
        receive: TReceive,
        send: TSend,
    ) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send

    def get_service_provider(self) -> "EllarInjector":
        return current_injector

    @cached_property
    def _get_websocket_context(self) -> IWebSocketHostContext:
        ws_context_factory: IWebSocketContextFactory = self.get_service_provider().get(
            IWebSocketContextFactory
        )
        return ws_context_factory(self)

    @cached_property
    def _get_http_context(self) -> IHTTPHostContext:
        http_context_factory: IHTTPConnectionContextFactory = (
            self.get_service_provider().get(IHTTPConnectionContextFactory)
        )
        return http_context_factory(self)

    def switch_to_http_connection(self) -> IHTTPHostContext:
        return self._get_http_context

    def switch_to_websocket(self) -> IWebSocketHostContext:
        return self._get_websocket_context

    def get_type(self) -> str:
        return str(self.scope["type"])

    def get_app(self) -> "App":
        return t.cast("App", self.scope["app"])

    def get_args(self) -> t.Tuple[TScope, TReceive, TSend]:
        return self.scope, self.receive, self.send

    @property
    def user(self) -> Identity:
        return self.scope["user"]  # type: ignore[no-any-return]

    @user.setter
    def user(self, value: t.Any) -> None:
        self.scope["user"] = value
