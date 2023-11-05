import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.common.exceptions import APIException
from ellar.common.interfaces import IExecutionContext
from starlette.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN


class GuardCanActivate(ABC, metaclass=ABCMeta):
    exception_class: t.Union[
        t.Type[HTTPException], t.Type[APIException]
    ] = HTTPException
    status_code: int = HTTP_403_FORBIDDEN
    detail: str = "Forbidden"

    @abstractmethod
    async def can_activate(self, context: IExecutionContext) -> bool:
        """Validate Route Context"""

    def raise_exception(self) -> None:
        raise self.exception_class(status_code=self.status_code, detail=self.detail)


GlobalGuard = t.NewType("GlobalGuard", GuardCanActivate)
