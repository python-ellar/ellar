from ellar.common import (
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule

from ellar_storage import StorageModule

from .controller import FileManagerController


@Module(modules=[HomeModule, StorageModule.register_setup()], controllers=[FileManagerController])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."}, status_code=404)
