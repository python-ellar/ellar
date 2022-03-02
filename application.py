import typing as t
from starlette.routing import BaseRoute

from starletteapi.controller import Controller
from starletteapi.main import StarletteApp
from starletteapi.module import ApplicationModule
from starletteapi.conf import Config
from starletteapi.templating import Environment


class _StarletteAppFactory:
    def __init__(self, app_module: t.Optional[ApplicationModule] = None):
        self.application_module = app_module or ApplicationModule()

    def _finalize_app_initialization(self, app: StarletteApp) -> None:
        app.injector.container.add_instance(app)
        app.injector.container.add_instance(app.config, Config)
        app.injector.container.add_instance(app.jinja_environment, Environment)
        self.application_module.module.on_app_ready(app)

    def _build_controller_routes(self) -> t.List[BaseRoute]:
        controllers = self.application_module.get_controllers()
        routes = []
        for controller in controllers:
            if isinstance(controller, Controller):
                routes.append(controller.get_route())
        return routes

    def _build_module_routes(self) -> t.List[BaseRoute]:
        module_routers = self.application_module.get_module_routers()
        routes = [module_router for module_router in module_routers]
        return routes

    def _get_application_events(self) -> t.Dict:
        events = dict(lifespan=None, on_startup=None, on_shutdown=None)
        _lifespan = self.application_module.module.get_lifespan()
        if _lifespan:
            events['lifespan'] = _lifespan
            return events

        events['on_startup'] = self.application_module.module.get_on_startup()
        events['on_shutdown'] = self.application_module.module.get_on_shutdown()
        return events

    def create_app(
            self, app_module: ApplicationModule
    ) -> StarletteApp:
        self.application_module = app_module
        routes = self._build_controller_routes() + self._build_module_routes()
        events = self._get_application_events()

        app = StarletteApp(
            routes=routes,
            root_module=app_module,
            **events
        )
        self._finalize_app_initialization(app=app)
        return app


StarletteAppFactory = _StarletteAppFactory()
