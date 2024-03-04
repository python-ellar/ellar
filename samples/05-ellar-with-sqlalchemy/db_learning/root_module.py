import ellar.common as ec
from ellar.app import App
from ellar.core import ModuleBase
from ellar_sql import EllarSQLModule, EllarSQLService

from db_learning.command import seed_user
from db_learning.controller import UsersController
from db_learning.pagination import list_api_router, list_template_router


@ec.Module(
    modules=[EllarSQLModule.register_setup()],
    routers=[list_template_router, list_api_router],
    controllers=[UsersController],
    commands=[seed_user],
)
class ApplicationModule(ModuleBase, ec.IApplicationStartup):
    async def on_startup(self, app: App) -> None:
        db_service = app.injector.get(EllarSQLService)
        db_service.create_all()

    @ec.exception_handler(404)
    def exception_404_handler(
        cls, ctx: ec.IExecutionContext, exc: Exception
    ) -> ec.Response:
        return ec.JSONResponse({"detail": "Resource not found."}, status_code=404)
