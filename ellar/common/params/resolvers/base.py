import typing as t
from abc import ABC, ABCMeta, abstractmethod

from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import MissingError
from pydantic.fields import ModelField

if t.TYPE_CHECKING:  # pragma: no cover
    from ..params import ParamFieldInfo


class RouteParameterModelField(ModelField):
    field_info: "ParamFieldInfo"


class IRouteParameterResolver(ABC, metaclass=ABCMeta):
    model_field: t.Union[RouteParameterModelField, ModelField]

    @abstractmethod
    @t.no_type_check
    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        """Resolve handle"""


class BaseRouteParameterResolver(IRouteParameterResolver, ABC):
    def __init__(self, model_field: ModelField, *args: t.Any, **kwargs: t.Any) -> None:
        self.model_field: RouteParameterModelField = t.cast(
            RouteParameterModelField, model_field
        )

    def assert_field_info(self) -> None:
        from .. import params

        assert isinstance(
            self.model_field.field_info, params.ParamFieldInfo
        ), "Params must be subclasses of Param"

    @classmethod
    def create_error(cls, loc: t.Any) -> ErrorWrapper:
        return ErrorWrapper(MissingError(), loc=loc)

    @classmethod
    def validate_error_sequence(cls, errors: t.Any) -> t.List[ErrorWrapper]:
        if not errors:
            return []
        return list(errors) if isinstance(errors, list) else [errors]

    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        value_ = await self.resolve_handle(*args, **kwargs)
        return value_

    @abstractmethod
    @t.no_type_check
    async def resolve_handle(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        """resolver action"""
