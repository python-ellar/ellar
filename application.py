import typing as t
from starlette.routing import BaseRoute

from starletteapi.controller import Controller
from starletteapi.main import StarletteApp
from starletteapi.module import ApplicationModule
from starletteapi.conf import Config
from starletteapi.templating import Environment


class StarletteAppFactory:
    @classmethod
    def _finalize_app_initialization(cls, app: StarletteApp, app_module: ApplicationModule) -> None:
        app.injector.container.add_instance(app)
        app.injector.container.add_instance(app.config, Config)
        app.injector.container.add_instance(app.jinja_environment, Environment)
        app_module.module.on_app_ready(app)

    @classmethod
    def _build_controller_routes(cls, app_module: ApplicationModule) -> t.List[BaseRoute]:
        controllers = app_module.get_controllers()
        routes = []
        for controller in controllers:
            if isinstance(controller, Controller):
                routes.append(controller.get_route())
        return routes

    @classmethod
    def _build_module_routes(cls, app_module: ApplicationModule) -> t.List[BaseRoute]:
        module_routers = app_module.get_module_routers()
        routes = [module_router for module_router in module_routers]
        return routes

    @classmethod
    def _get_application_events(cls, app_module: ApplicationModule) -> t.Dict:
        events = dict(lifespan=None, on_startup=None, on_shutdown=None)
        _lifespan = app_module.module.get_lifespan()
        if _lifespan:
            events['lifespan'] = _lifespan
            return events

        events['on_startup'] = app_module.module.get_on_startup()
        events['on_shutdown'] = app_module.module.get_on_shutdown()
        return events

    @classmethod
    def create_app(
            cls, app_module: ApplicationModule
    ) -> StarletteApp:
        routes = cls._build_controller_routes(app_module) + cls._build_module_routes(app_module)
        events = cls._get_application_events(app_module)

        app = StarletteApp(
            routes=routes,
            app_module=app_module,
            **events
        )
        cls._finalize_app_initialization(app=app, app_module=app_module)
        return app
