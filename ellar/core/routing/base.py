import typing as t
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    SCOPE_API_VERSIONING_RESOLVER,
    VERSIONING_KEY,
)
from ellar.common.interfaces import (
    IExecutionContext,
    IExecutionContextFactory,
    IGuardsConsumer,
    IInterceptorsConsumer,
)
from ellar.common.logging import request_logger
from ellar.common.types import TReceive, TScope, TSend
from ellar.core.context import current_injector
from ellar.reflect import reflect
from starlette.routing import Match

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import ControllerBase
    from ellar.core.versioning.resolver import BaseAPIVersioningResolver

__all__ = [
    "RouteOperationBase",
    "WebsocketRouteOperationBase",
]


class RouteOperationBase:
    methods: t.Set[str]
    _controller_type: t.Optional[t.Union[t.Type, t.Type["ControllerBase"]]] = None

    def __init__(self, endpoint: t.Callable) -> None:
        self.endpoint = endpoint
        _controller_type: t.Type = self.get_controller_type()

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

    @asynccontextmanager
    async def _ensure_dependency_availability(
        self, context: IExecutionContext
    ) -> t.AsyncGenerator:
        controller_type = context.get_class()
        module_scope_owner = next(
            context.get_app().injector.tree_manager.find_module(
                lambda data: controller_type in data.providers
                or controller_type in data.exports
            )
        )
        if module_scope_owner and module_scope_owner.is_ready:
            async with module_scope_owner.value.context():
                yield
        else:
            yield

    async def app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        request_logger.debug(
            f"Started Computing Execution Context - '{self.__class__.__name__}'"
        )

        execution_context_factory = current_injector.get(IExecutionContextFactory)
        context = execution_context_factory.create_context(
            operation=self, scope=scope, receive=receive, send=send
        )
        current_injector.update_scoped_context(IExecutionContext, context)

        interceptor_consumer = current_injector.get(IInterceptorsConsumer)
        guard_consumer = current_injector.get(IGuardsConsumer)

        request_logger.debug(
            f"Running Guards and Interceptors - '{self.__class__.__name__}'"
        )
        async with self._ensure_dependency_availability(context):
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
            return t.cast(t.Type, _controller_type)

        return self._controller_type

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
