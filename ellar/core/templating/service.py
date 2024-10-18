import os
import typing as t
from functools import lru_cache

import jinja2
from ellar.common import IHostContext
from ellar.common.interfaces import ITemplateRenderingService
from ellar.common.templating import TemplateResponse
from ellar.core import Config
from ellar.di import injectable, request_scope
from jinja2 import Environment
from starlette.background import BackgroundTask


@lru_cache(1200)
def get_template_name(template_name: str) -> str:
    # Split the filename and extension
    name, ext = os.path.splitext(template_name)

    # If there's no extension, add .html
    if not ext:
        return template_name + ".html"

    # Otherwise, return the original name
    return template_name


@injectable(scope=request_scope)
class TemplateRenderingService(ITemplateRenderingService):
    def __init__(self, config: Config, context: IHostContext) -> None:
        self.config = config
        self.context = context
        self.jinja_env = self.context.get_service_provider().get(Environment)

    def process_view_model(self, view_response: t.Any) -> t.Dict:
        if isinstance(view_response, dict):
            return view_response
        return {"model": view_response}

    def _compute_template_context(self, template_context: t.Dict) -> t.Dict:
        request = self.context.switch_to_http_connection().get_request()

        org_context = template_context.copy()
        for processor in self.config.APP_CONTEXT_PROCESSORS or []:
            res = processor(request)
            assert isinstance(
                res, dict
            ), f"{processor} is expected to return a dict object"
            template_context.update(res)

        template_context.update(org_context)

        return template_context

    def _get_jinja_and_template_context(
        self, template_name: str, **context: t.Any
    ) -> t.Tuple["jinja2.Template", t.Dict]:
        jinja_template = self.jinja_env.get_template(get_template_name(template_name))
        template_context = dict(context)
        return jinja_template, template_context

    def render_template(
        self,
        template_name: str,
        template_context: t.Dict[str, t.Any],
        background: t.Optional[BackgroundTask] = None,
        headers: t.Union[t.Mapping[str, str], None] = None,
        status_code: int = 200,
        response_type: t.Type[TemplateResponse] = TemplateResponse,
    ) -> TemplateResponse:
        jinja_template, template_context_ = self._get_jinja_and_template_context(
            template_name=template_name,
            **self.process_view_model(template_context),
        )
        template_context = self._compute_template_context(template_context_)
        return response_type(
            template=jinja_template,
            context=template_context,
            status_code=status_code,
            background=background,
            headers=headers,
        )

    def render_template_string(
        self, template_string: str, **template_context: t.Any
    ) -> str:
        try:
            jinja_template, template_context_ = self._get_jinja_and_template_context(
                template_name=template_string,
                **self.process_view_model(template_context),
            )
        except jinja2.TemplateNotFound:
            jinja_template = self.jinja_env.from_string(template_string)
            template_context_ = template_context

        template_context = self._compute_template_context(template_context_)

        return jinja_template.render(template_context)
