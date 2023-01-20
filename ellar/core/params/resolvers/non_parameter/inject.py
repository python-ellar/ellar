import inspect
import typing as t

from ellar.core.context import IExecutionContext
from ellar.types import T

from .base import NonParameterResolver


class ProviderParameterInjector(NonParameterResolver):
    """
    Defines `Provider` resolver for route parameter based on the provided `service`
    """

    def __init__(self, service: t.Optional[t.Type[T]] = None) -> None:
        if service:
            assert isinstance(service, type), "Service must be a type"
        super().__init__(data=service)

    def __call__(
        self, parameter_name: str, parameter_annotation: t.Type[T]
    ) -> "ProviderParameterInjector":
        self.parameter_name = parameter_name
        self.type_annotation = parameter_annotation
        if not self.data and isinstance(self.type_annotation, inspect.Parameter.empty):
            raise Exception("Injectable must have a valid type")

        if (
            self.data
            and parameter_annotation is not inspect.Parameter.empty
            and parameter_annotation is not self.data
        ):
            raise Exception(
                f"Annotation({self.type_annotation}) is not the same as service({self.data})"
            )

        if not self.data:
            self.data = self.type_annotation
        return self

    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        service_provider = ctx.get_service_provider()
        if not self.data:
            raise RuntimeError("ProviderParameterInjector not properly setup")
        value = service_provider.get(self.data)
        return {self.parameter_name: value}, []
