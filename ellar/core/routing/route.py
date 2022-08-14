import inspect
import typing as t

from starlette.concurrency import run_in_threadpool
from starlette.routing import Route as StarletteRoute, compile_path

from ellar.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    EXTRA_ROUTE_ARGS_KEY,
    NOT_SET,
    RESPONSE_OVERRIDE_KEY,
)
from ellar.core.context import ExecutionContext
from ellar.core.params import RequestEndpointArgsModel
from ellar.core.response.model import RouteResponseModel
from ellar.exceptions import ImproperConfiguration, RequestValidationError
from ellar.helper import generate_operation_unique_id, get_name
from ellar.reflect import reflect

from .base import RouteOperationBase

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.params import ExtraEndpointArg


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
        response: t.Mapping[int, t.Type],
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self._is_coroutine = inspect.iscoroutinefunction(endpoint)
        self._defined_responses: t.Dict[int, t.Type] = dict(response)

        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
        self.endpoint = endpoint  # type: ignore

        self.name = get_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema
        self.methods = self.get_methods(methods)

        self.endpoint_parameter_model: RequestEndpointArgsModel = NOT_SET
        self.response_model: RouteResponseModel = NOT_SET

        reflect.define_metadata(CONTROLLER_OPERATION_HANDLER_KEY, self, self.endpoint)
        self._load_model()

    def build_route_operation(  # type:ignore
        self,
        path_prefix: str = "",
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        **kwargs: t.Any,
    ) -> None:
        _path_changed = False
        if path_prefix not in ("", "/") and path_prefix not in self.path:
            self.path = f"{path_prefix.rstrip('/')}/{self.path.lstrip('/')}"
            self.path_regex, self.path_format, self.param_convertors = compile_path(
                self.path
            )
            _path_changed = True

        extra_route_args: t.List["ExtraEndpointArg"] = (
            reflect.get_metadata(EXTRA_ROUTE_ARGS_KEY, self.endpoint) or []
        )

        if self.endpoint_parameter_model is NOT_SET or _path_changed:
            self.endpoint_parameter_model = self.request_endpoint_args_model(
                path=self.path_format,
                endpoint=self.endpoint,
                operation_unique_id=self.get_operation_unique_id(methods=self.methods),
                param_converters=self.param_convertors,
                extra_endpoint_args=extra_route_args,
            )
            self.endpoint_parameter_model.build_model()
        self.include_in_schema = include_in_schema
        if name:
            self.name = f"{name}:{self.name}"

    def _load_model(self) -> None:
        self.build_route_operation()
        response_override: t.Union[t.Dict, t.Any] = reflect.get_metadata(
            RESPONSE_OVERRIDE_KEY, self.endpoint
        )
        if response_override:
            _response_override = response_override
            if not isinstance(_response_override, dict):
                raise ImproperConfiguration(
                    f"`RESPONSE_OVERRIDE` is must be of type `Dict` - {_response_override}"
                )
            self._defined_responses.update(_response_override)

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

    async def _handle_request(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)
        if self._is_coroutine:
            response_obj = await self.endpoint(**func_kwargs)
        else:
            response_obj = await run_in_threadpool(self.endpoint, **func_kwargs)
        response = self.response_model.process_response(
            ctx=context, response_obj=response_obj
        )
        await response(context.scope, context.receive, context.send)
