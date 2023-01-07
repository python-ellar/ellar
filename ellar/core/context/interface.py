import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.response import Response
from ellar.types import TReceive, TScope, TSend

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import ControllerBase
    from ellar.core.main import App
    from ellar.core.routing import RouteOperationBase
    from ellar.di.injector import EllarInjector


class IHTTPHostContext(ABC):
    @property
    @abstractmethod
    def has_response(self) -> bool:
        """checks if response was requested before send"""

    @abstractmethod
    def get_response(self) -> Response:
        """Gets response"""

    @abstractmethod
    def get_request(self) -> Request:
        """Returns Request instance"""

    @abstractmethod
    def get_client(self) -> HTTPConnection:
        """Returns HTTPConnection instance"""


class IWebSocketHostContext(ABC):
    @abstractmethod
    def get_client(self) -> WebSocket:
        """Returns WebSocket instance"""


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


class IExecutionContext(IHostContext, ABC):
    @abstractmethod
    def get_handler(self) -> t.Callable:
        """Gets operation handler"""

    @abstractmethod
    def get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        """Gets operation handler class"""


class IHostContextFactory(ABC):
    @abstractmethod
    def create_context(self) -> IHostContext:
        pass


class IExecutionContextFactory(ABC):
    @abstractmethod
    def create_context(self, operation: "RouteOperationBase") -> IExecutionContext:
        pass
