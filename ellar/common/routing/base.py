import typing as t
from abc import ABC, abstractmethod

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
    SCOPE_SERVICE_PROVIDER,
    VERSIONING_KEY,
)
from ellar.common.interfaces import (
    IExecutionContext,
    IExecutionContextFactory,
    IGuardsConsumer,
    IInterceptorsConsumer,
)
from ellar.common.logger import request_logger
from ellar.common.types import TReceive, TScope, TSend
from ellar.reflect import reflect
from starlette.routing import Match

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import ControllerBase
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver
    from ellar.di import EllarInjector

__all__ = [
    "RouteOperationBase",
    "WebsocketRouteOperationBase",
]


class RouteOperationBase:
    methods: t.Set[str]

    def __init__(self, endpoint: t.Callable) -> None:
        self.endpoint = endpoint
        _controller_type: t.Type = reflect.get_metadata(  # type: ignore[assignment]
            CONTROLLER_CLASS_KEY, self.endpoint
        )
        self._controller_type: t.Union[t.Type, t.Type["ControllerBase"]] = t.cast(
            t.Union[t.Type, t.Type["ControllerBase"]], _controller_type
        )

    # @t.no_type_check
    # def __call__(
    #     self, context: IExecutionContext, *args: t.Any, **kwargs: t.Any
    # ) -> t.Any:
    #     return self.endpoint(*args, **kwargs)

    @abstractmethod
    def _load_model(self) -> None:
        """compute route models"""

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        request_logger.debug(
            f"Started Computing Execution Context - '{self.__class__.__name__}'"
        )
        service_provider: "EllarInjector" = scope[SCOPE_SERVICE_PROVIDER]

        execution_context_factory = service_provider.get(IExecutionContextFactory)
        context = execution_context_factory.create_context(
            operation=self, scope=scope, receive=receive, send=send
        )
        service_provider.update_scoped_context(IExecutionContext, context)

        interceptor_consumer = service_provider.get(IInterceptorsConsumer)
        guard_consumer = service_provider.get(IGuardsConsumer)

        request_logger.debug(
            f"Running Guards and Interceptors - '{self.__class__.__name__}'"
        )
        await guard_consumer.execute(context, self)
        await interceptor_consumer.execute(context, self)

    def get_controller_type(self) -> t.Type:
        """
        For operation under a controller, `get_control_type` and `get_class` will return the same result
        For operation under ModuleRouter, this will return a unique type created for the router for tracking some properties
        :return: a type that wraps the operation
        """
        request_logger.debug(
            f"Resolving Endpoint Handler Controller Type - '{self.__class__.__name__}'"
        )
        if not self._controller_type:
            _controller_type = reflect.get_metadata(CONTROLLER_CLASS_KEY, self.endpoint)
            if _controller_type is None or not isinstance(_controller_type, type):
                raise Exception("Operation must have a single control type.")
            self._controller_type = t.cast(t.Type, _controller_type)

        return self._controller_type

    @abstractmethod
    async def handle_request(self, *, context: IExecutionContext) -> t.Any:
        """return a context"""

    @abstractmethod
    async def handle_response(
        self, context: IExecutionContext, response_obj: t.Any
    ) -> None:
        """returns a any"""

    def get_allowed_version(self) -> t.Set[t.Union[int, float, str]]:
        request_logger.debug(
            f"Resolving Endpoint Versions - '{self.__class__.__name__}'"
        )
        versions = reflect.get_metadata(VERSIONING_KEY, self.endpoint) or set()
        if not versions:
            versions = (
                reflect.get_metadata(VERSIONING_KEY, self.get_controller_type())
                or set()
            )
        return versions

    @classmethod
    def get_methods(cls, methods: t.Optional[t.List[str]] = None) -> t.Set[str]:
        if methods is None:
            methods = ["GET"]

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
                "BaseAPIVersioningResolver", scope[SCOPE_API_VERSIONING_RESOLVER]
            )
            if not version_scheme_resolver.can_activate(
                route_versions=self.get_allowed_version()
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
