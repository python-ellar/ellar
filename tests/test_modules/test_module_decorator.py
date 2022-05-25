from ellar.core import AppFactory
from ellar.core.modules import BaseModuleDecorator, ModuleBase, ModuleDecorator
from ellar.core.routing import ModuleRouterBase

from .sample import SampleModule


def test_module_contents():
    assert isinstance(
        SampleModule, (ModuleDecorator, BaseModuleDecorator)
    ), "SampleModule is not an instance of ModuleDecorator | BaseModuleDecorator"
    module_base = SampleModule.get_module()
    assert module_base, "SampleModule can not be None"
    assert isinstance(module_base, type) and issubclass(
        module_base, ModuleBase
    ), "Must be a type and a subclass of ModuleBase"

    assert module_base.get_module_decorator() == SampleModule
    before_initialisation = module_base.get_before_initialisation()

    assert len(before_initialisation) == 1
    assert (
        before_initialisation._handlers[0].handler.__name__
        == module_base.on_app_init_handler.__name__
    )

    after_initialisation = module_base.get_after_initialisation()
    assert (
        after_initialisation._handlers[0].handler.__name__
        == module_base.on_app_started_handler.__name__
    )
    assert len(after_initialisation) == 1

    module_middleware = module_base.get_middleware()
    assert len(module_middleware) == 1
    dispatch = module_middleware[0].options.get("dispatch")
    assert dispatch.__name__ == module_base.middleware.__name__

    exceptions_handlers = module_base.get_exceptions_handlers()
    assert len(exceptions_handlers) == 1
    assert exceptions_handlers.get(404).__name__ == module_base.exception_404.__name__

    on_startup = module_base.get_on_startup()
    assert len(on_startup) == 1
    assert (
        on_startup._handlers[0].handler.__name__
        == module_base.on_startup_handler.__name__
    )

    on_shutdown = module_base.get_on_shutdown()
    assert len(on_shutdown) == 1
    assert (
        on_shutdown._handlers[0].handler.__name__
        == module_base.on_shutdown_handler.__name__
    )


def test_module_get_routes_works():
    assert isinstance(
        SampleModule, (ModuleDecorator, BaseModuleDecorator)
    ), "SampleModule is not an instance of ModuleDecorator | BaseModuleDecorator"
    routes = SampleModule.get_routes()
    assert len(routes) == 4

    @ModuleDecorator()
    class AnotherSampleModuleGetRoute:
        pass

    routes = AnotherSampleModuleGetRoute.get_routes()
    assert len(routes) == 0


def test_module_get_module_routers_works():
    assert isinstance(
        SampleModule, (ModuleDecorator, BaseModuleDecorator)
    ), "SampleModule is not an instance of ModuleDecorator | BaseModuleDecorator"
    mounts = SampleModule.get_module_routers()

    assert len(mounts) == 2
    for item in mounts:
        assert isinstance(item, ModuleRouterBase)

    @ModuleDecorator()
    class AnotherSampleModuleGetModuleRouters:
        pass

    mounts = AnotherSampleModuleGetModuleRouters.get_module_routers()
    assert len(mounts) == 0


def test_module_installation():
    app = AppFactory.create_app()
    assert len(app.routes) == 0
    assert len(app._exception_handlers) == 2
    assert len(app._user_middleware) == 0
    assert len(app.root_module.templating_modules) == 1
    assert len(app.on_startup) == 0
    assert len(app.on_shutdown) == 0

    app.install_module(SampleModule)
    assert len(app.routes) == 4
    assert len(app._exception_handlers) == 3
    assert len(app._user_middleware) == 1
    assert len(app.root_module.templating_modules) == 2
    assert len(app.on_startup) == 1
    assert len(app.on_shutdown) == 1
