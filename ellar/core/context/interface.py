import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.response import Response

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import ControllerBase
    from ellar.core.main import App
    from ellar.core.routing import RouteOperationBase
    from ellar.di.injector import RequestServiceProvider


class ExecutionContextException(Exception):
    pass


class IExecutionContext(ABC, metaclass=ABCMeta):
    @abstractmethod
    def set_operation(self, operation: t.Optional["RouteOperationBase"] = None) -> None:
        """re-inits operation handler"""

    @property
    @abstractmethod
    def has_response(self) -> bool:
        """checks if response was requested before send"""

    @abstractmethod
    def get_service_provider(self) -> "RequestServiceProvider":
        """Gets  RequestServiceProvider instance"""

    @abstractmethod
    def switch_to_request(self) -> Request:
        """Returns Request instance"""

    @abstractmethod
    def switch_to_http_connection(self) -> HTTPConnection:
        """Returns HTTPConnection instance"""

    @abstractmethod
    def switch_to_websocket(self) -> WebSocket:
        """Returns WebSocket instance"""

    @abstractmethod
    def get_response(self) -> Response:
        """Gets response"""

    @abstractmethod
    def get_app(self) -> "App":
        """Gets application instance"""

    def get_handler(self) -> t.Callable:
        """Gets operation handler"""

    def get_class(self) -> t.Optional[t.Type["ControllerBase"]]:
        """Gets operation handler class"""
