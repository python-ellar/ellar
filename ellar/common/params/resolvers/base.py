import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.pydantic import (
    ModelField,
    get_missing_field_error,
    regenerate_error_with_loc,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from ..params import ParamFieldInfo


class ResolverResult(t.NamedTuple):
    """
    A named tuple containing the resolved value, any errors, and the raw data.
    """

    data: t.Optional[t.Any]
    errors: t.Optional[t.List[t.Dict[str, t.Any]]]
    raw_data: t.Dict[str, t.Any]


class RouteParameterModelField(ModelField):
    field_info: "ParamFieldInfo"


class IRouteParameterResolver(ABC, metaclass=ABCMeta):
    model_field: t.Union[RouteParameterModelField, ModelField]

    @abstractmethod
    @t.no_type_check
    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> ResolverResult:
        """
        Resolves the value of the parameter during request processing.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            `ResolverResult`: A named tuple containing the resolved value, any errors, and the raw data.
        """

    @abstractmethod
    @t.no_type_check
    def create_raw_data(
        self, data: t.Any, field_name: t.Optional[str] = None
    ) -> t.Dict:
        """
        Creates the raw data for the parameter.

        Args:
            data: The resolved value of the parameter.
            field_name: The name of the field.

        Returns:
            `dict`: A dictionary containing the raw data.
        """


class BaseRouteParameterResolver(IRouteParameterResolver, ABC):
    def __init__(self, model_field: ModelField, *args: t.Any, **kwargs: t.Any) -> None:
        self.model_field: RouteParameterModelField = t.cast(
            RouteParameterModelField, model_field
        )

    def create_raw_data(
        self, data: t.Any, field_name: t.Optional[str] = None
    ) -> t.Dict:
        return {field_name or self.model_field.name: data}

    def assert_field_info(self) -> None:
        """
        Asserts that the field info is of the correct type.
        """
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

    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> ResolverResult:
        value_ = await self.resolve_handle(*args, **kwargs)
        return value_

    @abstractmethod
    @t.no_type_check
    async def resolve_handle(
        self,
        *args: t.Any,
        alias: t.Optional[str] = None,
        name: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> ResolverResult:
        """
        Resolves the value of the parameter during request processing.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
            alias: The alias of the parameter. Optional.
            name: The name of the parameter. Optional.

        Returns:
            `ResolverResult`: A named tuple containing the resolved value, any errors, and the raw data.
        """
