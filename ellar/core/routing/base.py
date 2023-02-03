import typing as t
from abc import ABC, abstractmethod

from starlette.routing import Match

from ellar.constants import (
    CONTROLLER_CLASS_KEY,
    GUARDS_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
    SCOPE_SERVICE_PROVIDER,
    VERSIONING_KEY,
)
from ellar.core.context import IExecutionContext, IExecutionContextFactory
from ellar.di import EllarInjector
from ellar.reflect import reflect
from ellar.services.reflector import Reflector
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
        reflector = context.get_service_provider().get(Reflector)
        app = context.get_app()

        targets = [self.endpoint, self.get_control_type()]

        _guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = reflector.get_all_and_override(GUARDS_KEY, *targets)

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
        context = execution_context_factory.create_context(
            operation=self, scope=scope, receive=receive, send=send
        )

        await self.run_route_guards(context=context)
        await self._handle_request(context=context)

    def get_control_type(self) -> t.Type:
        """
        For operation under a controller, `get_control_type` and `get_class` will return the same result
        For operation under ModuleRouter, this will return a unique type created for the router for tracking some properties
        :return: a type that wraps the operation
        """
        if not hasattr(self, "_control_type"):
            _control_type = reflect.get_metadata(CONTROLLER_CLASS_KEY, self.endpoint)
            if _control_type is None:
                raise Exception("Operation must have a single control type.")
            self._control_type = t.cast(t.Type, _control_type)

        return self._control_type

    @abstractmethod
    async def _handle_request(self, *, context: IExecutionContext) -> None:
        """return a context"""

    def get_allowed_version(self) -> t.Set[t.Union[int, float, str]]:
        versions = reflect.get_metadata(VERSIONING_KEY, self.endpoint) or set()
        if not versions:
            versions = (
                reflect.get_metadata(VERSIONING_KEY, self.get_control_type()) or set()
            )
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
