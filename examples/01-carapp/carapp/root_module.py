from ellar.common import (
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule

from .apps.car.module import CarModule
from .commands import db, whatever_you_want


@Module(modules=[HomeModule, CarModule], commands=[db, whatever_you_want])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."})
