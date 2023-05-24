import typing as t
from abc import ABC, abstractmethod

from ..interfaces import IExecutionContext


class EllarInterceptor(ABC):
    @abstractmethod
    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        """implementation comes here"""
