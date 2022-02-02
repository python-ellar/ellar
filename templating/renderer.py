from functools import wraps, lru_cache
from typing import Callable, Optional, Any, cast, Dict

from starlette.routing import iscoroutinefunction_or_partial

from starletteapi.responses import Response
from starlette.templating import _TemplateResponse # noqa
from .environment import Environment
from starletteapi.routing.operations import ExtraOperationArgs, OperationMeta, ControllerOperation
from starletteapi.routing.route_models.param_resolvers import inject
from starletteapi.context import ExecutionContext
from ..constants import NOT_SET
from ..helper import get_name


@lru_cache(1200)
def get_template_name(template_name: str) -> str:
    if not template_name.endswith(".html"):
        return template_name + ".html"
    return template_name


class _RenderOperation:
    def __init__(self, *, func: Callable, template_name: str, use_mvc: bool = False) -> None:
        self.use_mvc = use_mvc
        self.execution_ctx = ExtraOperationArgs(
            name="execution_ctx", annotation=ExecutionContext, default_value=inject()
        )
        self.jinja_environment = ExtraOperationArgs(
            name="jinja_environment", annotation=Environment, default_value=inject()
        )
        self.func = func
        self.template_name = template_name
        self.set_arg()

    def _get_template_name(self, ctx: ExecutionContext):
        template_name = self.template_name
        if self.use_mvc and isinstance(ctx.operation, ControllerOperation):
            operation = cast(ControllerOperation, ctx.operation)
            instance = ctx.get_service_provider().get(operation.controller_class)
            template_name = instance.full_view_name(self.template_name)
        return get_template_name(template_name)

    def _create_template_response(
            self,
            jinja_environment: Environment,
            ctx: ExecutionContext,
            view_response: Any
    ) -> _TemplateResponse:
        template_name = self._get_template_name(ctx=ctx)
        template_context = dict(request=ctx.switch_to_request())
        template_context.update(**self.process_view_model(view_response))

        template = jinja_environment.get_template(template_name)
        response = _TemplateResponse(template=template, context=template_context)
        return response

    def get_view_function(self) -> Callable:
        def as_view(*args: Any, **kw: Any) -> Any:
            execution_ctx = self.execution_ctx.resolve_args(kw)
            jinja_environment = self.jinja_environment.resolve_args(kw)
            view_response = self.func(*args, **kw)

            if isinstance(view_response, Response):
                return view_response
            return self._create_template_response(jinja_environment, execution_ctx, view_response)
        return as_view

    def set_arg(self):
        args = cast(OperationMeta, getattr(self.func, "_meta", OperationMeta()))
        args.extra_route_args += [self.execution_ctx, self.jinja_environment]
        args.response_override = _TemplateResponse
        setattr(self.func, "_meta", args)

    @classmethod
    def process_view_model(cls, view_response: Any) -> Dict:
        if isinstance(view_response, dict):
            return view_response
        return dict(model=view_response)


class _AsyncRenderOperation(_RenderOperation):
    def get_view_function(self) -> Callable:
        async def as_view(*args: Any, **kw: Any) -> Any:
            execution_ctx = self.execution_ctx.resolve_args(kw)
            jinja_environment = self.jinja_environment.resolve_args(kw)
            view_response = await self.func(*args, **kw)

            if isinstance(view_response, Response):
                return view_response
            return self._create_template_response(jinja_environment, execution_ctx, view_response)
        return as_view


class Render:
    def __init__(self, template_name: Optional[str] = NOT_SET) -> None:
        if template_name is not NOT_SET:
            assert isinstance(template_name, str), "Render Operation must invoked eg. @Render()"
        self.template_name = None if template_name is NOT_SET else template_name
        self.use_mvc = self.template_name is None

    def __call__(self, func: Callable) -> Callable:
        endpoint_name = get_name(func)
        _render_operation = _RenderOperation

        if iscoroutinefunction_or_partial(func):
            _render_operation = _AsyncRenderOperation

        operation = _render_operation(
            func=func, template_name=self.template_name or endpoint_name,
            use_mvc=self.use_mvc
        )
        endpoint = wraps(operation.func)(operation.get_view_function())
        return endpoint
