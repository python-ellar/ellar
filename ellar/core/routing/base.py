import typing as t
from abc import ABC, abstractmethod

from starlette.routing import Match

from ellar.constants import (
    GUARDS_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
    SCOPE_SERVICE_PROVIDER,
    VERSIONING_KEY,
)
from ellar.core.context import IExecutionContext, IExecutionContextFactory
from ellar.di import EllarInjector
from ellar.reflect import reflect
from ellar.types import TReceive, TScope, TSend

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.guard import GuardCanActivate
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver

__all__ = [
    "RouteOperationBase",
    "WebsocketRouteOperationBase",
]


class RouteOperationBase:
    path: str
    endpoint: t.Callable
    methods: t.Set[str]

    @t.no_type_check
    def __call__(
        self, context: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        return self.endpoint(*args, **kwargs)

    @abstractmethod
    def _load_model(self) -> None:
        """compute route models"""

    @t.no_type_check
    async def run_route_guards(self, context: IExecutionContext) -> None:
        app = context.get_app()
        _guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = reflect.get_metadata(GUARDS_KEY, self.endpoint)

        if not _guards:
            _guards = app.get_guards()

        if _guards:
            for guard in _guards:
                if isinstance(guard, type):
                    guard = context.get_service_provider().get(guard)

                result = await guard.can_activate(context)
                if not result:
                    guard.raise_exception()

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        service_provider = t.cast(EllarInjector, scope[SCOPE_SERVICE_PROVIDER])

        execution_context_factory = service_provider.get(IExecutionContextFactory)
        context = execution_context_factory.create_context(operation=self)

        await self.run_route_guards(context=context)
        await self._handle_request(context=context)

    @abstractmethod
    async def _handle_request(self, *, context: IExecutionContext) -> None:
        """return a context"""

    @abstractmethod
    def build_route_operation(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Full operation initialization"""

    def get_allowed_version(self) -> t.Set[t.Union[int, float, str]]:
        versions = reflect.get_metadata(VERSIONING_KEY, self.endpoint) or set()
        return t.cast(t.Set[t.Union[int, float, str]], versions)

    @classmethod
    def get_methods(cls, methods: t.Optional[t.List[str]] = None) -> t.Set[str]:
        if methods is None:
            methods = ["GET"]

        _methods = {method.upper() for method in methods}
        # if "GET" in _methods:
        #     _methods.add("HEAD")

        return _methods

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        match = super().matches(scope)  # type: ignore
        if match[0] is Match.FULL:
            version_scheme_resolver: "BaseAPIVersioningResolver" = t.cast(
                "BaseAPIVersioningResolver", scope[SCOPE_API_VERSIONING_RESOLVER]
            )
            if not version_scheme_resolver.can_activate(
                route_versions=self.get_allowed_version()
            ):
                return Match.NONE, {}
        return match  # type: ignore

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self.endpoint)


class WebsocketRouteOperationBase(RouteOperationBase, ABC):
    methods: t.Set[str] = {"WS"}  # just to avoid attribute error
