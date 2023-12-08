from ellar.common import (
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import LazyModuleImport as lazyLoad
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule


@Module(
    modules=[HomeModule, lazyLoad("auth_project_with_handler.auth.module:AuthModule")]
)
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."})
