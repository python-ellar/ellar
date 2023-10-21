from ellar.common import IHostContext, JSONResponse, Module, Response, exception_handler
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule

from .car.module import CarModule


@Module(modules=[HomeModule, CarModule])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, context: IHostContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."})
