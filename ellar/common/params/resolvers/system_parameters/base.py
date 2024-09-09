import typing as t
from abc import ABC, abstractmethod

from ellar.common.exceptions import ImproperConfiguration
from ellar.common.interfaces import IExecutionContext
from ellar.common.types import T

from ..base import IRouteParameterResolver, ResolverResult


class SystemParameterResolver(IRouteParameterResolver, ABC):
    """
    Define extra route function parameter dependencies that does not depend on user inputs

    Example:
    >>> class UserField(SystemParameterResolver):
    >>>     async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> t.Any:
    >>>          request = ctx.switch_to_http_connection().get_request()
    >>>          user = request.get('user', None)
    >>>          if user:
    >>>             return {self.parameter_name: user}, []
    >>>          return {}, [ErrorWrapper(exc=Exception('Authenticated Users Only'), loc=self.parameter_name)]
    Usage:
    >>> @get('/abc')
    >>> def abc(user: User = UserField()):
    >>>     return user
    """

    in_: str = "system_parameter"

    def __init__(self, data: t.Optional[t.Any] = None):
        self.data = data
        self.parameter_name: t.Optional[str] = None
        self.type_annotation: t.Optional[t.Type] = None

    def __call__(self, parameter_name: str, parameter_annotation: t.Type[T]) -> t.Any:
        self.parameter_name = parameter_name
        self.type_annotation = parameter_annotation
        return self

    def create_raw_data(self, data: t.Any) -> t.Dict:
        return {self.parameter_name: data}

    @abstractmethod
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError


class BaseConnectionParameterResolver(SystemParameterResolver):
    """
    Defines HTTPConnection fields resolver for route parameter based on the provided `lookup_connection_field`
    """

    # Look up field in ctx.switch_to_connection().get_client().lookup_connection_field
    lookup_connection_field: t.Optional[str]

    def __call__(
        self, parameter_name: str, parameter_annotation: t.Type[T]
    ) -> "SystemParameterResolver":
        result = super().__call__(parameter_name, parameter_annotation)
        if not hasattr(self, "lookup_connection_field"):
            raise ImproperConfiguration(
                f"{self.__class__.__name__}.request_field is not set"
            )
        return result  # type: ignore

    async def get_value(self, ctx: IExecutionContext) -> t.Any:
        assert self.lookup_connection_field

        connection = ctx.switch_to_http_connection().get_client()
        return connection.get(self.lookup_connection_field)

    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> ResolverResult:
        value = await self.get_value(ctx)
        return ResolverResult(
            {self.parameter_name: value}, [], raw_data=self.create_raw_data(value)
        )
