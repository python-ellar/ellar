import typing as t

from ellar.core.context import ExecutionContext, IExecutionContext
from ellar.core.templating import Environment, TemplateResponse
from ellar.core.templating.renderer import get_template_name, process_view_model

from ..responses import Response
from .base import ResponseModel


class HTMLResponseModelRuntimeError(RuntimeError):
    pass


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
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        self.response_type = t.cast(t.Type[TemplateResponse], self.response_type)

        jinja_environment = context.get_service_provider().get(Environment)
        template_name = self._get_template_name(ctx=context)
        template_context = dict(request=context.switch_to_request())
        template_context.update(**process_view_model(response_obj))
        template = jinja_environment.get_template(template_name)

        response_args, headers = self.get_context_response(context=context)
        response_args.update(template=template, context=template_context)
        response = self._response_type(**response_args, headers=headers)
        return response

    def _get_template_name(self, ctx: IExecutionContext) -> str:
        template_name = self.template_name
        exe_ctx = t.cast(ExecutionContext, ctx)
        if self.use_mvc:
            controller_class = exe_ctx.get_class()
            if not controller_class:
                raise HTMLResponseModelRuntimeError(
                    "cannot find Controller in request context"
                )
            template_name = controller_class.full_view_name(self.template_name)
        return get_template_name(template_name)
