import inspect
import typing as t
import warnings
from functools import lru_cache

import jinja2
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse

from architek.context import ExecutionContext
from architek.response import Response
from architek.response.model import ResponseModel
from architek.routing import set_meta
from architek.routing.operations import OperationBase

from ..constants import NOT_SET
from ..helper import get_name
from ..requests import Request
from .environment import Environment

if t.TYPE_CHECKING:
    from architek.controller import ControllerBase


@lru_cache(1200)
def get_template_name(template_name: str) -> str:
    if not template_name.endswith(".html"):
        return template_name + ".html"
    return template_name


class HTMLResponseModel(ResponseModel):
    def __init__(
        self,
        template_name: str,
        response_type: t.Type[_TemplateResponse] = _TemplateResponse,
        use_mvc: bool = False,
    ) -> None:
        super().__init__(response_type=response_type)
        self.template_name = template_name
        self.use_mvc = use_mvc

    @classmethod
    def process_view_model(cls, view_response: t.Any) -> t.Dict:
        if isinstance(view_response, dict):
            return view_response
        return dict(model=view_response)

    def create_response(
        self, context: ExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        self.response_type = t.cast(t.Type[_TemplateResponse], self.response_type)

        jinja_environment = context.get_service_provider().get(Environment)
        template_name = self._get_template_name(ctx=context)
        template_context = dict(request=context.switch_to_request())
        template_context.update(**self.process_view_model(response_obj))
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
        if not callable(func) or isinstance(func, OperationBase):
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


def _get_jinja_and_template_context(
    template_name: str, request: Request, **context: t.Any
) -> t.Tuple["jinja2.Template", t.Dict]:
    jinja_environment = request.service_provider.get(Environment)
    jinja_template = jinja_environment.get_template(get_template_name(template_name))
    template_context = dict(context)
    template_context.update(request=request)
    return jinja_template, template_context


def render_template_string(
    template_name: str, request: Request, **context: t.Any
) -> str:
    """Renders a template to string.
    :param request: current request object
    :param template_name: the name of the template to be rendered
    :param context: variables that should be available in the context of the template.
    """
    jinja_template, template_context = _get_jinja_and_template_context(
        template_name=template_name, request=request, **context
    )

    return jinja_template.render(template_context)


def render_template(
    template_name: str,
    request: Request,
    context: t.Dict = {},
    background: BackgroundTask = None,
) -> _TemplateResponse:
    """Renders a template from the template folder with the given context.
    :param request: current request object
    :param template_name: the name of the template to be rendered
    :param context: variables that should be available in the context of the template.
    :param background: any background task to be executed after render.
    :return TemplateResponse
    """
    jinja_template, template_context = _get_jinja_and_template_context(
        template_name=template_name,
        request=request,
        **HTMLResponseModel.process_view_model(context),
    )
    return _TemplateResponse(
        template=jinja_template, context=template_context, background=background
    )
