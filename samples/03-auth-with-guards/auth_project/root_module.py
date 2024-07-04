from datetime import timedelta

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
from ellar_jwt import JWTModule


@Module(
    modules=[
        HomeModule,
        lazyLoad("auth_project.auth.module:AuthModule"),
        JWTModule.setup(
            signing_secret_key="my_poor_secret_key_lol", lifetime=timedelta(minutes=5)
        ),
    ]
)
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(self, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."})
