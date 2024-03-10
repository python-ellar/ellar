from ellar.common import (
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import ModuleBase
from ellar.di import Container
from ellar_django import DjangoModule

from .apps.event.module import EventModule
from .interfaces.events_repository import IEventRepository


@Module(
    modules=[
        DjangoModule.setup(settings_module="ellar_and_django_orm.wsgi_django.settings"),
        EventModule,
    ]
)
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."}, status_code=404)

    def register_services(self, container: Container) -> None:
        from .services.event_repository import EventRepository

        container.register(IEventRepository, EventRepository)
