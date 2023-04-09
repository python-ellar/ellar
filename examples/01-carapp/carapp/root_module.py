from ellar.common import exception_handler
from ellar.core import ModuleBase
from ellar.core.context import IExecutionContext
from ellar.core.response import JSONResponse, Response
from ellar.samples.modules import HomeModule
from ellar.common import Module
from .commands import db, whatever_you_want
from .apps.car.module import CarModule


@Module(modules=[HomeModule, CarModule], commands=[db, whatever_you_want])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))
