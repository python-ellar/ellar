from ellar.common import IExecutionContext, Module, exception_handler
from ellar.common.responses import JSONResponse, Response
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule

from .apps.car.module import CarModule
from .commands import db, whatever_you_want


@Module(modules=[HomeModule, CarModule], commands=[db, whatever_you_want])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."})
