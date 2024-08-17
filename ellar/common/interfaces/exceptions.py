import typing as t
from abc import ABC, abstractmethod

from starlette.responses import Response

from .context import IHostContext


class IExceptionHandler(ABC, t.Iterable):
    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, IExceptionHandler):
            return other.exception_type_or_code == self.exception_type_or_code
        return False

    def __iter__(self) -> t.Iterator:
        as_tuple = (self.exception_type_or_code, self)
        return iter(as_tuple)

    exception_type_or_code: t.Optional[t.Union[int, t.Type[Exception]]] = None

    @abstractmethod
    async def catch(self, ctx: IHostContext, exc: t.Any) -> t.Union[Response, t.Any]:  #
        """Catch implementation"""

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        assert (
            cls.exception_type_or_code
        ), f"'exception_type_or_code' must be defined. {cls}"
        if not isinstance(cls.exception_type_or_code, int):
            assert issubclass(
                cls.exception_type_or_code, Exception
            ), "'exception_type_or_code' is not a valid type"


class IExceptionMiddlewareService:
    @abstractmethod
    def build_exception_handlers(
        self, *exception_handlers: IExceptionHandler
    ) -> "IExceptionMiddlewareService":
        """Build Exception Handlers"""

    @abstractmethod
    def get_500_error_handler(
        self,
    ) -> t.Optional[IExceptionHandler]:
        """Gets 500 Error Handler"""
