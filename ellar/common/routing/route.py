import inspect
import typing as t

from ellar.common.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    EXTRA_ROUTE_ARGS_KEY,
    NOT_SET,
    RESPONSE_OVERRIDE_KEY,
)
from ellar.common.exceptions import ImproperConfiguration, RequestValidationError
from ellar.common.interfaces import IExecutionContext
from ellar.common.logger import request_logger
from ellar.common.params import ExtraEndpointArg, RequestEndpointArgsModel
from ellar.common.responses.models import RouteResponseModel
from ellar.common.utils import generate_operation_unique_id, get_name
from ellar.reflect import reflect
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response
from starlette.routing import Route as StarletteRoute
from starlette.routing import compile_path

from .base import RouteOperationBase


class RouteOperation(RouteOperationBase, StarletteRoute):
    methods: t.Set[str]
    request_endpoint_args_model: t.Type[
        RequestEndpointArgsModel
    ] = RequestEndpointArgsModel

    __slots__ = (
        "endpoint",
        "_is_coroutine",
        "endpoint_parameter_model",
        "response_model",
        "_defined_responses",
    )

    def __init__(
        self,
        *,
        path: str,
        methods: t.List[str],
        endpoint: t.Callable,
        response: t.Mapping[int, t.Union[t.Type, t.Any]],
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        super().__init__(endpoint=endpoint)
        self._is_coroutine = inspect.iscoroutinefunction(endpoint)
        self._defined_responses: t.Dict[int, t.Type] = dict(response)

        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )

        self.name = get_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema
        self.methods = self.get_methods(methods)

        self.endpoint_parameter_model: RequestEndpointArgsModel = NOT_SET
        self.response_model: RouteResponseModel = NOT_SET

        reflect.define_metadata(CONTROLLER_OPERATION_HANDLER_KEY, self, self.endpoint)
        self._load_model()

    def _load_model(self) -> None:
        extra_route_args: t.Union[t.List["ExtraEndpointArg"], "ExtraEndpointArg"] = (
            reflect.get_metadata(EXTRA_ROUTE_ARGS_KEY, self.endpoint) or []
        )
        if not isinstance(extra_route_args, list):  # pragma: no cover
            extra_route_args = [extra_route_args]

        if self.endpoint_parameter_model is NOT_SET:
            self.endpoint_parameter_model = self.request_endpoint_args_model(
                path=self.path_format,
                endpoint=self.endpoint,
                operation_unique_id=self.get_operation_unique_id(methods=self.methods),
                param_converters=self.param_convertors,
                extra_endpoint_args=extra_route_args,
            )
        self.endpoint_parameter_model.build_model()

        response_override: t.Union[t.Dict, t.Any] = reflect.get_metadata(
            RESPONSE_OVERRIDE_KEY, self.endpoint
        )
        if response_override:
            if not isinstance(response_override, dict):
                raise ImproperConfiguration(
                    f"`RESPONSE_OVERRIDE` is must be of type `Dict` - {response_override}"
                )
            self._defined_responses.update(response_override)

        self.response_model = RouteResponseModel(
            route_responses=self._defined_responses  # type: ignore
        )

    def get_operation_unique_id(
        self, methods: t.Union[t.Set[str], t.Sequence[str], str]
    ) -> str:
        _methods: t.Sequence[str] = (
            list(methods) if isinstance(methods, set) else [t.cast(str, methods)]
        )
        return generate_operation_unique_id(
            name=self.name, path=self.path_format, methods=_methods
        )

    async def run(self, context: IExecutionContext, kwargs: t.Dict) -> t.Any:
        request_logger.debug(
            f"Executing Request Endpoint Handler - '{self.__class__.__name__}'"
        )
        if self._is_coroutine:
            return await self.endpoint(**kwargs)
        else:
            return await run_in_threadpool(self.endpoint, **kwargs)

    async def handle_request(self, context: IExecutionContext) -> t.Any:
        request_logger.debug(
            f"Resolving Request Endpoint Handler Dependencies - '{self.__class__.__name__}'"
        )
        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)

        return await self.run(context, func_kwargs)

    async def handle_response(
        self, context: IExecutionContext, response_obj: t.Any
    ) -> None:
        request_logger.debug(f"Processing Response - '{self.__class__.__name__}'")
        response = self.response_model.process_response(
            ctx=context, response_obj=response_obj
        )
        if isinstance(response, Response):
            await response(*context.get_args())
