import typing as t
from abc import ABC, abstractmethod

from starlette.responses import Response

from ellar.core.context import IExecutionContext


class IExceptionHandler(ABC, t.Iterable):
    def __iter__(self) -> t.Iterator:
        as_tuple = (self.exception_type_or_code, self)
        return iter(as_tuple)

    exception_type_or_code: t.Optional[t.Union[int, t.Type[Exception]]] = None

    @abstractmethod
    async def catch(
        self, ctx: IExecutionContext, exc: t.Any
    ) -> t.Union[Response, t.Any]:  #
        pass

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        assert (
            cls.exception_type_or_code
        ), f"exception_type_or_code must be defined. {cls}"


class IExceptionMiddlewareService:
    @abstractmethod
    def build_exception_handlers(self) -> None:
        pass

    @abstractmethod
    def get_500_error_handler(
        self,
    ) -> t.Optional[IExceptionHandler]:
        pass
