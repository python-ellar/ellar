import inspect
import warnings
from functools import lru_cache
from typing import Callable, Optional, Any, cast, Dict, Type, Union
from starletteapi.responses import Response
from starletteapi.responses.model import ResponseModel
from starlette.templating import _TemplateResponse  # noqa
from .environment import Environment
from starletteapi.routing.operations import OperationMeta, ControllerOperation, OperationBase, Operation
from starletteapi.context import ExecutionContext
from ..constants import NOT_SET
from ..helper import get_name


@lru_cache(1200)
def get_template_name(template_name: str) -> str:
    if not template_name.endswith(".html"):
        return template_name + ".html"
    return template_name


class HTMLResponseModel(ResponseModel):
    def __init__(self, response_type: Type[_TemplateResponse], template_name: str, use_mvc: bool = False) -> None:
        super().__init__(response_type=response_type)
        self.template_name = template_name
        self.use_mvc = use_mvc

    @classmethod
    def process_view_model(cls, view_response: Any) -> Dict:
        if isinstance(view_response, dict):
            return view_response
        return dict(model=view_response)

    def create_response(self, context: ExecutionContext, response_obj: Any, status_code: int) -> Response:
        self.response_type = cast(Type[_TemplateResponse], self.response_type)

        jinja_environment = context.get_service_provider().get(Environment)
        template_name = self._get_template_name(ctx=context)
        template_context = dict(request=context.switch_to_request())
        template_context.update(**self.process_view_model(response_obj))
        template = jinja_environment.get_template(template_name)

        response_args, headers = self.get_context_response(context=context)
        response_args.update(template=template, context=template_context)
        response = self.response_type(**response_args)
        if headers:
            response.headers.raw.extend(headers)
        return response

    def _get_template_name(self, ctx: ExecutionContext):
        template_name = self.template_name
        if self.use_mvc and isinstance(ctx.operation, ControllerOperation):
            operation = cast(ControllerOperation, ctx.operation)
            template_name = operation.controller.full_view_name(self.template_name)
        return get_template_name(template_name)


class Render:
    def __init__(self, template_name: Optional[str] = NOT_SET) -> None:
        if template_name is not NOT_SET:
            assert isinstance(template_name, str), "Render Operation must invoked eg. @Render()"
        self.template_name = None if template_name is NOT_SET else template_name
        self.use_mvc = self.template_name is None

    def __call__(self, func: Union[Callable, Any]) -> Union[Callable, Any]:
        if not callable(func) or isinstance(func, OperationBase):
            warnings.warn_explicit(
                UserWarning(
                    f"\n@Render should be used only as a function decorator. "
                    f"\nUse @Render before @Method decorator."
                ),
                category=None,
                filename=inspect.getfile(getattr(func, 'endpoint', func)),
                lineno=inspect.getsourcelines(getattr(func, 'endpoint', func))[1],
                source=None,
            )
            return func

        endpoint_name = get_name(func)
        args = cast(OperationMeta, getattr(func, "_meta", OperationMeta()))
        args.response_override = HTMLResponseModel(
            _TemplateResponse, template_name=self.template_name or endpoint_name, use_mvc=self.use_mvc
        )
        setattr(func, "_meta", args)
        return func
