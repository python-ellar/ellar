import typing as t
from abc import ABC, abstractmethod

from ellar.common import APIException, IExecutionContext

from ..handlers.schemes import APIKeyCookie, APIKeyHeader, APIKeyQuery
from .mixin import GuardAuthMixin


class GuardAPIKeyQuery(APIKeyQuery, GuardAuthMixin, ABC):
    openapi_in: str = "query"
    exception_class = APIException

    @abstractmethod
    async def authentication_handler(
        self,
        context: IExecutionContext,  # type:ignore[override]
        key: t.Optional[t.Any],
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover


class GuardAPIKeyCookie(APIKeyCookie, GuardAuthMixin, ABC):
    openapi_in: str = "cookie"
    exception_class = APIException

    @abstractmethod
    async def authentication_handler(
        self,
        context: IExecutionContext,  # type:ignore[override]
        key: t.Optional[t.Any],
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover


class GuardAPIKeyHeader(APIKeyHeader, GuardAuthMixin, ABC):
    openapi_in: str = "header"
    exception_class = APIException

    @abstractmethod
    async def authentication_handler(
        self,
        context: IExecutionContext,  # type:ignore[override]
        key: t.Optional[t.Any],
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover
