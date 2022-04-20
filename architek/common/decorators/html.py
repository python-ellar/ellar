import inspect
import typing as t
import warnings

from architek.constants import NOT_SET
from architek.core.context import ExecutionContext
from architek.core.helper import get_name
from architek.core.response import Response
from architek.core.response.model import ResponseModel
from architek.core.routing import RouteBase
from architek.core.templating import Environment, TemplateResponse
from architek.core.templating.renderer import get_template_name, process_view_model

from .base import set_meta

if t.TYPE_CHECKING:
    from architek.core.routing.controller import ControllerBase


class HTMLResponseModel(ResponseModel):
    def __init__(
        self,
        template_name: str,
        response_type: t.Type[TemplateResponse] = TemplateResponse,
        use_mvc: bool = False,
    ) -> None:
        super().__init__(response_type=response_type)
        self.template_name = template_name
        self.use_mvc = use_mvc

    def create_response(
        self, context: ExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        self.response_type = t.cast(t.Type[TemplateResponse], self.response_type)

        jinja_environment = context.get_service_provider().get(Environment)
        template_name = self._get_template_name(ctx=context)
        template_context = dict(request=context.switch_to_request())
        template_context.update(**process_view_model(response_obj))
        template = jinja_environment.get_template(template_name)

        response_args, headers = self.get_context_response(context=context)
        response_args.update(template=template, context=template_context)
        response = self.response_type(**response_args, headers=headers)
        return response

    def _get_template_name(self, ctx: ExecutionContext) -> str:
        template_name = self.template_name
        if self.use_mvc and ctx.controller_type:
            controller_class: t.Type["ControllerBase"] = ctx.controller_type
            template_name = controller_class.full_view_name(self.template_name)
        return get_template_name(template_name)


class Render:
    def __init__(self, template_name: t.Optional[str] = NOT_SET) -> None:
        if template_name is not NOT_SET:
            assert isinstance(
                template_name, str
            ), "Render Operation must invoked eg. @Render()"
        self.template_name = None if template_name is NOT_SET else template_name
        self.use_mvc = self.template_name is None

    def __call__(self, func: t.Union[t.Callable, t.Any]) -> t.Union[t.Callable, t.Any]:
        if not callable(func) or isinstance(func, RouteBase):
            warnings.warn_explicit(
                UserWarning(
                    "\n@Render should be used only as a function decorator. "
                    "\nUse @Render before @Method decorator."
                ),
                category=None,
                filename=inspect.getfile(getattr(func, "endpoint", func)),
                lineno=inspect.getsourcelines(getattr(func, "endpoint", func))[1],
                source=None,
            )
            return func

        endpoint_name = get_name(func)

        response = HTMLResponseModel(
            template_name=self.template_name or endpoint_name, use_mvc=self.use_mvc
        )
        target_decorator = set_meta("response_override", {200: response})
        return target_decorator(func)
