import typing as t

from starlette.concurrency import run_in_threadpool
from starlette.routing import (
    Route as StarletteRoute,
    compile_path,
    iscoroutinefunction_or_partial,
)

from architek.constants import NOT_SET
from architek.core.context import ExecutionContext
from architek.core.operation_meta import OperationMeta
from architek.core.params import RequestEndpointArgsModel
from architek.core.response.model import RouteResponseModel
from architek.exceptions import RequestValidationError
from architek.helper import generate_operation_unique_id, get_name

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
        "_meta",
        "response_model",
        "_defined_responses",
    )

    def __init__(
        self,
        *,
        path: str,
        methods: t.List[str],
        endpoint: t.Callable,
        response: t.Union[t.Type, t.Dict[int, t.Type]],
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self._is_coroutine = iscoroutinefunction_or_partial(endpoint)
        self._defined_responses = response

        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = path
        self.endpoint = endpoint  # type: ignore

        self.name = get_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema
        self.methods = self.get_methods(methods)

        self.endpoint_parameter_model: RequestEndpointArgsModel = NOT_SET
        self.response_model: RouteResponseModel = NOT_SET
        _meta = getattr(self.endpoint, "_meta", {})
        self._meta: OperationMeta = OperationMeta(**_meta)

        self._meta.update(
            operation_handler=self.endpoint,
        )
        self._load_model()

    def _load_model(self) -> None:
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
        self.endpoint_parameter_model = self.request_endpoint_args_model(
            path=self.path_format,
            endpoint=self.endpoint,
            operation_unique_id=self.get_operation_unique_id(
                method=list(self.methods)[0]
            ),
        )

        if self._meta.extra_route_args:
            self.endpoint_parameter_model.add_extra_route_args(
                *self._meta.extra_route_args
            )
        self.endpoint_parameter_model.build_model()

        if self._meta.response_override:
            _response_override = self._meta.response_override
            if not isinstance(_response_override, dict):
                _response_override = {200: _response_override}  # type: ignore
            self._defined_responses.update(_response_override)  # type: ignore

        self.response_model = RouteResponseModel(
            route_responses=self._defined_responses
        )

    def get_operation_unique_id(self, method: str) -> str:
        return generate_operation_unique_id(
            name=self.name, path=self.path_format, method=method
        )

    async def _handle(self, context: ExecutionContext) -> None:
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

    def __hash__(self) -> int:
        return hash((self.path, tuple(self.methods)))
