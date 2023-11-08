import typing as t
from abc import ABC, ABCMeta, abstractmethod, abstractproperty

from ellar.common.constants import empty_receive
from ellar.common.types import T, TReceive, TScope, TSend
from ellar.di import injectable, request_scope
from starlette.requests import empty_send
from starlette.responses import Response

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app import App
    from ellar.common.models import ControllerBase, Identity
    from ellar.common.routing import RouteOperationBase
    from ellar.core import HTTPConnection, Request, WebSocket
    from ellar.di.injector import EllarInjector


class IHTTPHostContext(ABC):
    @property
    @abstractmethod
    def has_response(self) -> bool:
        """checks if response was requested before send"""

    @abstractmethod
    def get_response(self) -> "Response":
        """Gets response"""

    @abstractmethod
    def get_request(self) -> "Request":
        """Returns Request instance"""

    @abstractmethod
    def get_client(self) -> "HTTPConnection":
        """Returns HTTPConnection instance"""


class IWebSocketHostContext(ABC):
    @abstractmethod
    def get_client(self) -> "WebSocket":
        """Returns WebSocket instance"""


@injectable(scope=request_scope)
class IHostContext(ABC, metaclass=ABCMeta):
    @abstractmethod
    def get_service_provider(self) -> "EllarInjector":
        """Gets  RequestServiceProvider instance"""

    @abstractmethod
    def switch_to_http_connection(self) -> IHTTPHostContext:
        """Returns HTTPConnection instance"""

    @abstractmethod
    def switch_to_websocket(self) -> IWebSocketHostContext:
        """Returns WebSocket instance"""

    @abstractmethod
    def get_app(self) -> "App":
        """Gets application instance"""

    @abstractmethod
    def get_type(self) -> str:
        """returns scope type"""

    @abstractmethod
    def get_args(self) -> t.Tuple[TScope, TReceive, TSend]:
        """returns all args passed to asgi function"""

    @abstractproperty
    def user(self) -> "Identity":
        """gets user identity"""

    @user.setter
    def user(self, value: t.Any) -> None:
        """Sets user identity"""


@injectable(scope=request_scope)
class IExecutionContext(IHostContext, ABC):
    @abstractmethod
    def get_handler(self) -> t.Callable:
        """Gets operation handler"""

    @abstractmethod
    def get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        """Gets operation handler controller class"""


class IHostContextFactory(ABC):
    @abstractmethod
    def create_context(
        self,
        scope: TScope,
        receive: TReceive = empty_receive,
        send: TSend = empty_send,
    ) -> IHostContext:
        """Create Context Action"""


class IExecutionContextFactory(ABC):
    @abstractmethod
    def create_context(
        self,
        operation: "RouteOperationBase",
        scope: TScope,
        receive: TReceive = empty_receive,
        send: TSend = empty_send,
    ) -> IExecutionContext:
        """Create Context Action"""


class SubHostContextFactory(t.Generic[T], ABC):
    """
    Factory for creating HostContext types and validating them.
    """

    context_type: t.Type[T]

    __slots__ = ()

    def __call__(self, context: IHostContext) -> T:
        self.validate(context)
        return self.create_context_type(context)

    @abstractmethod
    def validate(self, context: IHostContext) -> None:
        """Validation Action"""

    def create_context_type(self, context: IHostContext) -> T:
        scope, receive, send = context.get_args()
        return self.context_type(  # type:ignore
            scope=scope,
            receive=receive,
            send=send,
        )


class IHTTPConnectionContextFactory(SubHostContextFactory[IHTTPHostContext], ABC):
    context_typ: t.Type[IHTTPHostContext]


class IWebSocketContextFactory(SubHostContextFactory[IWebSocketHostContext], ABC):
    context_type: t.Type[IWebSocketHostContext]
