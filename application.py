import typing as t
from starletteapi.main import StarletteApp
from starletteapi.module import ApplicationModule


class StarletteAppFactory:
    @classmethod
    def create_app(
            cls, app_module: t.Union[ApplicationModule, t.Type]
    ) -> StarletteApp:
        assert isinstance(app_module, ApplicationModule), "Only ApplicationModule is allowed"

        routes = app_module.build_controller_routes() + app_module.build_module_routes()
        events = app_module.get_application_events()

        app = StarletteApp(
            routes=routes,
            global_guards=app_module.global_guards,
            app_module=None,
            **events
        )
        return app
