import typing as t
from abc import ABC, abstractmethod

from pydantic.fields import ModelField

from ellar.core.context import IExecutionContext

from ..response_types import Response


class IResponseModel(ABC):
    # TODO: abstract to a interface package

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
