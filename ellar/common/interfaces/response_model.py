import typing as t
from abc import ABC, abstractmethod

from pydantic.fields import ModelField
from starlette.responses import Response

from .context import IExecutionContext


class IResponseModel(ABC):
    @property
    def media_type(self) -> str:  # pragma: no cover
        return "text/plain"

    @property
    def description(self) -> str:  # pragma: no cover
        return ""

    @abstractmethod
    def get_model_field(
        self,
    ) -> t.Optional[t.Union[ModelField, t.Any]]:  # pragma: no cover
        """Gets Model Fields"""

    @abstractmethod
    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:  # pragma: no cover
        """Create final response"""
