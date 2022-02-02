from abc import ABC, abstractmethod
from typing import Optional, Any

from starlette.exceptions import HTTPException
from starletteapi.status import HTTP_403_FORBIDDEN
from starletteapi.requests import HTTPConnection
from starletteapi.context import ExecutionContext


class GuardCanActivate(ABC):
    _exception_class: HTTPException = HTTPException
    _status_code: int = HTTP_403_FORBIDDEN
    _detail: str = "Not authenticated"

    @abstractmethod
    async def can_activate(self, context: ExecutionContext) -> bool:
        pass

    def raise_exception(self):
        raise self._exception_class(
            status_code=self._status_code, detail=self._detail
        )


class AuthGuard(GuardCanActivate, ABC):
    @abstractmethod
    async def handle_request(self, *, connection: HTTPConnection) -> Optional[Any]:
        pass

    async def can_activate(self, context: ExecutionContext) -> bool:
        connection = context.switch_to_http_connection()
        result = await self.handle_request(connection=connection)
        if result:
            # auth parameter on request
            return True
        return False
