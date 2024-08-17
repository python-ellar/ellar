import typing as t

from ellar.common.interfaces import IExecutionContext, ITemplateRenderingService
from ellar.common.logging import request_logger
from ellar.common.templating import TemplateResponse

from ..response_types import Response
from .base import ResponseModel


class HTMLResponseModelRuntimeError(RuntimeError):
    pass


class HTMLResponseModel(ResponseModel):
    response_type: t.Type[TemplateResponse] = TemplateResponse

    def __init__(
        self,
        template_name: str,
        use_mvc: bool = False,
    ) -> None:
        super().__init__(model_field_or_schema=str)
        self.template_name = template_name
        self.use_mvc = use_mvc

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        request_logger.debug(
            f"Creating Response from returned Handler value - '{self.__class__.__name__}'"
        )
        template_name = self._get_template_name(ctx=context)
        rendering_service: ITemplateRenderingService = (
            context.get_service_provider().get(ITemplateRenderingService)
        )

        response_args, headers = self.get_context_response(context=context)
        return rendering_service.render_template(
            template_name=template_name,
            template_context=response_obj,
            headers=headers,
            **response_args,
            response_type=self.response_type,
        )

    def _get_template_name(self, ctx: IExecutionContext) -> str:
        template_name = self.template_name
        if self.use_mvc:
            controller_class = ctx.get_class()
            if not controller_class or not hasattr(controller_class, "full_view_name"):
                raise HTMLResponseModelRuntimeError(
                    "cannot find Controller in request context"
                )
            template_name = controller_class.full_view_name(self.template_name)
        return template_name
