from datetime import timedelta

from ellar.common import (
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule
from ellar_jwt import JWTModule

from .auth.module import AuthModule
from .users.module import UsersModule


@Module(
    modules=[
        HomeModule,
        UsersModule,
        AuthModule,
        JWTModule.setup(
            signing_secret_key="my_secret", leeway=0, lifetime=timedelta(minutes=5)
        ),
    ]
)
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."})
