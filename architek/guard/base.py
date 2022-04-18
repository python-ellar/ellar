import typing as t
from abc import ABC, ABCMeta, abstractmethod

from starlette.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from architek.context import ExecutionContext
from architek.requests import HTTPConnection


class GuardCanActivate(ABC, metaclass=ABCMeta):
    _exception_class: t.Type[HTTPException] = HTTPException
    _status_code: int = HTTP_403_FORBIDDEN
    _detail: str = "Not authenticated"

    @abstractmethod
    async def can_activate(self, context: ExecutionContext) -> bool:
        pass

    def raise_exception(self) -> None:
        raise self._exception_class(status_code=self._status_code, detail=self._detail)


class BaseAuthGuard(GuardCanActivate, ABC, metaclass=ABCMeta):
    openapi_scope: t.List = []

    @abstractmethod
    async def handle_request(self, *, connection: HTTPConnection) -> t.Optional[t.Any]:
        pass

    @classmethod
    @abstractmethod
    def get_guard_scheme(cls) -> t.Dict:
        pass

    async def can_activate(self, context: ExecutionContext) -> bool:
        connection = context.switch_to_http_connection()
        result = await self.handle_request(connection=connection)
        if result:
            # auth parameter on request
            return True
        return False
