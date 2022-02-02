from typing import List, Sequence, Dict, Optional, Type
from starlette.middleware import Middleware
from starlette.routing import BaseRoute
from starletteapi.controller import ControllerBase, Controller
from starletteapi.main import StarletteApp
from starletteapi.module import ApplicationModule
from starletteapi.settings import Config
from starletteapi.templating import Environment


class _StarletteAppFactory:
    def __init__(self, app_module: Optional[ApplicationModule] = None):
        self.application_module = app_module or ApplicationModule()

    def _get_middleware(self) -> Sequence[Middleware]:
        middleware = list(self.application_module.middleware)
        return middleware

    def _finalize_app_initialization(self, app: StarletteApp) -> None:
        app.injector.container.add_instance(app)
        app.injector.container.add_instance(app.config, Config)
        app.injector.container.add_instance(app.jinja_environment, Environment)
        app.injector.container.add_exact_scoped(ControllerBase)

    def _build_controller_routes(self) -> List[BaseRoute]:
        controllers = self.application_module.get_controllers()
        routes = []
        for controller in controllers:
            if isinstance(controller, type) and issubclass(controller, ControllerBase):
                routes.append(controller.get_route())
                continue
            if isinstance(controller, Controller):
                routes.append(controller.mount)
                continue
        return routes

    def _build_module_routes(self) -> List[BaseRoute]:
        module_routers = self.application_module.get_module_routers()
        routes = [module_router for module_router in module_routers]
        return routes

    def _get_application_events(self) -> Dict:
        events = dict(lifespan=None, on_startup=None, on_shutdown=None)
        _lifespan = self.application_module.get_lifespan()
        if _lifespan:
            events['lifespan'] = _lifespan
            return events

        events['on_startup'] = self.application_module.get_on_startup()
        events['on_shutdown'] = self.application_module.get_on_shutdown()
        return events

    def create_app(
            self, app_module: ApplicationModule, config: Type[Config] = None
    ) -> StarletteApp:
        self.application_module = app_module
        routes = self._build_controller_routes() + self._build_module_routes()
        middleware = self._get_middleware()
        events = self._get_application_events()
        exception_handlers = self._get_registered_exception_handlers()

        # TODO: fix config base_url if config is None
        # if not config:
        #
        #     config = type(
        #         Config.__name__, (Config, ),
        #         {'__module__': Path(inspect.getfile(app_module.module)).resolve().parent}
        #     )
        app = StarletteApp(
            routes=routes,
            root_module=app_module.module,
            middleware=middleware,
            exception_handlers=exception_handlers,
            guards=self.application_module.guards,
            config=config,
            **events
        )
        modules = [app_module] + app_module.get_modules()
        app.add_modules(*modules)
        self._finalize_app_initialization(app=app)
        return app

    def _get_registered_exception_handlers(self):
        exception_handlers = self.application_module.register_custom_exceptions({})
        return exception_handlers


StarletteAppFactory = _StarletteAppFactory()
