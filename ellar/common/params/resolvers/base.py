import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.pydantic import (
    ModelField,
    get_missing_field_error,
    regenerate_error_with_loc,
)

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
    def create_error(cls, loc: t.Any) -> t.Any:
        return get_missing_field_error(loc=loc)

    @classmethod
    def validate_error_sequence(cls, errors: t.Any) -> t.List[t.Any]:
        if not errors:
            return []
        return regenerate_error_with_loc(errors=errors, loc_prefix=())

    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        value_ = await self.resolve_handle(*args, **kwargs)
        return value_

    @abstractmethod
    @t.no_type_check
    async def resolve_handle(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        """resolver action"""
