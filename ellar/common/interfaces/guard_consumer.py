import typing as t
from abc import ABC, abstractmethod

from .context import IExecutionContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.routing import RouteOperationBase


class IGuardsConsumer(ABC):
    @abstractmethod
    async def execute(
        self, context: IExecutionContext, route_operation: "RouteOperationBase"
    ) -> t.Any:
        """implementation goes here"""
