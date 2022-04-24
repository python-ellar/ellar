import typing as t
from abc import ABC, ABCMeta, abstractmethod

from architek.core.compatible import AttributeDictAccess, DataMapper
from architek.core.connection import HTTPConnection, Request, WebSocket
from architek.core.response import Response

if t.TYPE_CHECKING:
    from architek.core.main import ArchitekApp
    from architek.core.routing import RouteOperationBase
    from architek.di.injector import RequestServiceProvider


class ExecutionContextException(Exception):
    pass


class OperationExecutionMeta(DataMapper, AttributeDictAccess):
    pass


class IExecutionContext(ABC, metaclass=ABCMeta):
    @property
    @abstractmethod
    def operation(self) -> OperationExecutionMeta:
        pass

    @abstractmethod
    def set_operation(self, operation: t.Optional["RouteOperationBase"] = None) -> None:
        pass

    @property
    @abstractmethod
    def has_response(self) -> bool:
        pass

    @abstractmethod
    def get_service_provider(self) -> "RequestServiceProvider":
        pass

    @abstractmethod
    def switch_to_request(self) -> Request:
        pass

    @abstractmethod
    def switch_to_http_connection(self) -> HTTPConnection:
        pass

    @abstractmethod
    def switch_to_websocket(self) -> WebSocket:
        pass

    @abstractmethod
    def get_response(self) -> Response:
        pass

    @abstractmethod
    def get_app(self) -> "ArchitekApp":
        pass
