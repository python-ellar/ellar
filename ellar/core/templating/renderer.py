import typing as t
from functools import lru_cache

import jinja2
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse as TemplateResponse

from ellar.core.connection import Request

from .environment import Environment


@lru_cache(1200)
def get_template_name(template_name: str) -> str:
    if not template_name.endswith(".html"):
        return template_name + ".html"
    return template_name


def process_view_model(view_response: t.Any) -> t.Dict:
    if isinstance(view_response, dict):
        return view_response
    return dict(model=view_response)


def _get_jinja_and_template_context(
    template_name: str, request: Request, **context: t.Any
) -> t.Tuple["jinja2.Template", t.Dict]:
    jinja_environment = request.service_provider.get(Environment)
    jinja_template = jinja_environment.get_template(get_template_name(template_name))
    template_context = dict(context)
    template_context.update(request=request)
    return jinja_template, template_context


def render_template_string(
    template_name: str, request: Request, **template_kwargs: t.Any
) -> str:
    """Renders a template to string.
    :param request: Request instance
    :param template_name: the name of the template to be rendered
    :param template_kwargs: variables that should be available in the context of the template.
    """
    jinja_template, template_context = _get_jinja_and_template_context(
        template_name=template_name, request=request, **template_kwargs
    )

    return jinja_template.render(template_context)


def render_template(
    template_name: str,
    request: Request,
    background: BackgroundTask = None,
    **template_kwargs: t.Any
) -> TemplateResponse:
    """Renders a template from the template folder with the given context.
    :param request: Request instance
    :param template_name: the name of the template to be rendered
    :param template_kwargs: variables that should be available in the context of the template.
    :param background: any background task to be executed after render.
    :return TemplateResponse
    """
    jinja_template, template_context = _get_jinja_and_template_context(
        template_name=template_name,
        request=request,
        **process_view_model(template_kwargs),
    )
    return TemplateResponse(
        template=jinja_template, context=template_context, background=background
    )
