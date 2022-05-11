import typing as t
from abc import ABC, abstractmethod

from starlette.routing import Match

from ellar.constants import SCOPE_API_VERSIONING_RESOLVER
from ellar.core.context import ExecutionContext
from ellar.core.operation_meta import OperationMeta
from ellar.types import TReceive, TScope, TSend

if t.TYPE_CHECKING:
    from ellar.core.guard import GuardCanActivate
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver

__all__ = [
    "RouteOperationBase",
    "WebsocketRouteOperationBase",
]


class RouteOperationBase:
    _meta: OperationMeta

    endpoint: t.Callable

    @t.no_type_check
    def __call__(
        self, context: ExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        return self.endpoint(*args, **kwargs)

    @abstractmethod
    def _load_model(self) -> None:
        pass

    def get_guards(
        self,
    ) -> t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]:
        return list(self._meta.route_guards)

    def get_meta(self) -> OperationMeta:
        return self._meta

    def update_operation_meta(self, **kwargs: t.Any) -> None:
        self._meta.update(**kwargs)

    async def run_route_guards(self, context: ExecutionContext) -> None:
        app = context.get_app()
        _guards = self.get_guards() or app.get_guards()
        if _guards:
            for guard in _guards:
                if isinstance(guard, type):
                    guard = guard()
                result = await guard.can_activate(context)
                if not result:
                    guard.raise_exception()

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        context = ExecutionContext.create_context(
            scope=scope, receive=receive, send=send, operation=self
        )
        await self.run_route_guards(context=context)
        await self._handle_request(context=context)

    @abstractmethod
    async def _handle_request(self, *, context: ExecutionContext) -> None:
        """return a context"""

    @abstractmethod
    def build_route_operation(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Full operation initialization"""

    def get_allowed_version(self) -> t.Set[t.Union[int, float, str]]:
        return self._meta.route_versioning

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
        if match[0] is not Match.NONE:
            version_scheme_resolver: "BaseAPIVersioningResolver" = t.cast(
                "BaseAPIVersioningResolver", scope[SCOPE_API_VERSIONING_RESOLVER]
            )
            if not version_scheme_resolver.can_activate(
                route_versions=self.get_allowed_version()
            ):
                return Match.NONE, {}
        return match  # type: ignore


class WebsocketRouteOperationBase(RouteOperationBase, ABC):
    pass
