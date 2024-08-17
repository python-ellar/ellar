import typing as t
from abc import ABC, abstractmethod
from functools import cached_property

from ellar.common import constants
from ellar.common.interfaces import (
    IExecutionContext,
    IExecutionContextFactory,
    IGuardsConsumer,
    IInterceptorsConsumer,
)
from ellar.common.logging import request_logger
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.execution_context import current_injector
from ellar.di import register_request_scope_context
from ellar.reflect import reflect
from starlette.routing import Match

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver

__all__ = [
    "RouteOperationBase",
    "WebsocketRouteOperationBase",
]


class RouteOperationBase:
    methods: t.Set[str]

    def __init__(self, endpoint: t.Callable) -> None:
        self.endpoint = endpoint

    @cached_property
    def router_reflect_key(self) -> t.Any:
        return (
            reflect.get_metadata("ROUTER_REFLECT_KEY", self.endpoint)
            or constants.NOT_SET
        )

    @abstractmethod
    def _load_model(self) -> None:
        """compute route models"""

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        request_logger.debug(
            f"Started Computing Execution Context - '{self.__class__.__name__}'"
        )

        execution_context_factory = current_injector.get(IExecutionContextFactory)
        context = execution_context_factory.create_context(
            operation=self, scope=scope, receive=receive, send=send
        )
        register_request_scope_context(IExecutionContext, context)

        interceptor_consumer = current_injector.get(IInterceptorsConsumer)
        guard_consumer = current_injector.get(IGuardsConsumer)

        request_logger.debug(
            f"Running Guards and Interceptors - '{self.__class__.__name__}'"
        )

        await guard_consumer.execute(context, self)
        await interceptor_consumer.execute(context, self)

    def get_controller_type(self) -> t.Any:
        """
        For operation under a controller, `get_control_type` and `get_class` will return the same result
        For operation under ModuleRouter, this will return a unique type created for the router for tracking some properties
        :return: a type that wraps the operation
        """

        return self.router_reflect_key

    @abstractmethod
    async def handle_request(
        self, *, context: IExecutionContext
    ) -> t.Any:  # pragma: no cover
        """return a context"""

    @abstractmethod
    async def handle_response(
        self, context: IExecutionContext, response_obj: t.Any
    ) -> None:  # pragma: no cover
        """returns a any"""

    @cached_property
    def allowed_version(self) -> t.Set[t.Union[int, float, str]]:
        request_logger.debug(
            f"Resolving Endpoint Versions - '{self.__class__.__name__}'"
        )
        versions = (
            reflect.get_metadata(constants.VERSIONING_KEY, self.endpoint) or set()
        )
        if not versions:
            versions = (
                reflect.get_metadata(
                    constants.VERSIONING_KEY, self.get_controller_type()
                )
                or set()
            )
        return versions

    @classmethod
    def get_methods(cls, methods: t.Optional[t.List[str]] = None) -> t.Set[str]:
        methods = ["GET"] if not methods else methods

        _methods = {method.upper() for method in methods}
        # if "GET" in _methods:
        #     _methods.add("HEAD")

        return _methods

    def matches(self, scope: TScope) -> t.Tuple[Match, TScope]:
        request_logger.debug(
            f"Matching Endpoint URL, path={scope['path']}- '{self.__class__.__name__}'"
        )

        match = super().matches(scope)  # type: ignore
        if match[0] is Match.FULL:
            version_scheme_resolver: "BaseAPIVersioningResolver" = t.cast(
                "BaseAPIVersioningResolver",
                scope[constants.SCOPE_API_VERSIONING_RESOLVER],
            )
            if not version_scheme_resolver.can_activate(
                route_versions=self.allowed_version
            ):
                request_logger.debug(
                    f"URL Matched with invalid Version - '{self.__class__.__name__}'"
                )
                return Match.NONE, {}
        return match  # type: ignore

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self.endpoint)


class WebsocketRouteOperationBase(RouteOperationBase, ABC):
    methods: t.Set[str] = {"WS"}  # just to avoid attribute error
