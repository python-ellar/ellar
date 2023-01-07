import typing as t

from ellar.compatible import cached_property
from ellar.constants import SCOPE_SERVICE_PROVIDER
from ellar.types import TReceive, TScope, TSend

from .interface import IHostContext, IHTTPHostContext, IWebSocketHostContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.main import App
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
        return self._service_provider  # type:ignore

    @cached_property
    def _service_provider(self) -> "EllarInjector":
        return self.scope[SCOPE_SERVICE_PROVIDER]  # type:ignore

    def switch_to_http_connection(self) -> IHTTPHostContext:
        return self.get_service_provider().get(IHTTPHostContext)  # type: ignore

    def switch_to_websocket(self) -> IWebSocketHostContext:
        return self.get_service_provider().get(IWebSocketHostContext)  # type: ignore

    def get_type(self) -> str:
        return str(self.scope["type"])

    def get_app(self) -> "App":
        return t.cast("App", self.scope["app"])

    def get_args(self) -> t.Tuple[TScope, TReceive, TSend]:
        return self.scope, self.receive, self.send
