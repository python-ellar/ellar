import typing as t

from ellar.common.interfaces import ITemplateRenderingService
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse as TemplateResponse


def render_template_string(template_string: str, **template_context: t.Any) -> str:
    """Renders a template to string.
    :param template_string: Template String
    :param template_context: variables that should be available in the context of the template.
    """
    from ellar.core.execution_context import current_injector

    rendering_service: ITemplateRenderingService = current_injector.get(
        ITemplateRenderingService
    )
    return rendering_service.render_template_string(
        template_string=template_string, **template_context
    )


def render_template(
    template_name: str,
    background: t.Optional[BackgroundTask] = None,
    headers: t.Union[t.Mapping[str, str], None] = None,
    status_code: int = 200,
    **template_kwargs: t.Any,
) -> TemplateResponse:
    """Renders a template from the template folder with the given context.
    :param status_code: Template Response status code
    :param template_name: the name of the template to be rendered
    :param headers: Response Headers
    :param template_kwargs: variables that should be available in the context of the template.
    :param background: any background task to be executed after render.
    :return TemplateResponse
    """
    from ellar.core.execution_context import current_injector

    rendering_service: ITemplateRenderingService = current_injector.get(
        ITemplateRenderingService
    )
    return rendering_service.render_template(
        template_name=template_name,
        template_context=template_kwargs,
        background=background,
        status_code=status_code,
        headers=headers,
    )
