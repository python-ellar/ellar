import typing as t
from abc import ABC, abstractmethod

from pydantic.fields import ModelField

from ellar.core.context import IExecutionContext

from ..responses import Response


class IResponseModel(ABC):
    # TODO: abstract to a interface package

    media_type: str
    description: str

    @abstractmethod
    def get_model_field(self) -> t.Optional[t.Union[ModelField, t.Any]]:
        """Gets Model Fields"""

    @abstractmethod
    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        """Create final response"""
