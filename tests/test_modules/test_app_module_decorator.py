import pytest

from ellar.core.factory import AppFactoryModule
from ellar.core.modules import (
    ApplicationModuleDecorator,
    BaseModuleDecorator,
    ModuleBase,
    ModuleDecorator,
    ModuleDecoratorBuilder,
)
from ellar.core.modules.schema import ModuleData
from ellar.core.routing import ModuleRouterBase
from ellar.di import StarletteInjector
from ellar.exceptions import ImproperConfiguration

from .sample import (
    ModuleBaseExample,
    SampleApplicationModule,
    SampleController,
    SampleModule,
    mr,
)


def test_app_module_contents():
    assert isinstance(
        SampleApplicationModule, (ModuleDecorator, BaseModuleDecorator)
    ), "SampleApplicationModule is not an instance of ModuleDecorator | BaseModuleDecorator"

    module_base = SampleApplicationModule.get_module()
    assert module_base, "SampleApplicationModule can not be None"

    assert isinstance(module_base, type) and issubclass(
        module_base, ModuleBase
    ), "Must be a type and a subclass of ModuleBase"

    assert module_base.get_module_decorator() == SampleApplicationModule

    assert len(module_base.get_before_initialisation()) == 0
    assert len(module_base.get_after_initialisation()) == 0
    assert len(module_base.get_middleware()) == 0

    exceptions_handlers = module_base.get_exceptions_handlers()
    assert len(exceptions_handlers) == 1
    assert (
        exceptions_handlers.get(404).__name__
        == module_base.exception_404_override.__name__
    )

    assert len(module_base.get_on_startup()) == 0
    assert len(module_base.get_on_shutdown()) == 0


def test_module_get_routes_works():
    assert isinstance(
        SampleApplicationModule,
        (ModuleDecorator, BaseModuleDecorator, ApplicationModuleDecorator),
    ), "SampleApplicationModule is not an instance of ModuleDecorator | BaseModuleDecorator"

    routes = SampleApplicationModule.get_routes()
    assert len(routes) == 0

    @ApplicationModuleDecorator(routers=(mr,), controllers=(SampleController,))
    class AnotherSampleAppModuleGetRoute:
        pass

    routes = AnotherSampleAppModuleGetRoute.get_routes()
    assert len(routes) == 4


def test_module_get_module_routers_works():
    assert isinstance(
        SampleApplicationModule,
        (ModuleDecorator, BaseModuleDecorator, ApplicationModuleDecorator),
    ), "SampleModule is not an instance of ModuleDecorator | BaseModuleDecorator"
    mounts = SampleApplicationModule.get_module_routers()

    assert len(mounts) == 2
    for item in mounts:
        assert isinstance(item, ModuleRouterBase)

    @ApplicationModuleDecorator()
    class AnotherSampleAppModuleGetModuleRouters:
        pass

    mounts = AnotherSampleAppModuleGetModuleRouters.get_module_routers()
    assert len(mounts) == 0


def test_app_module_build_turns_module_data():
    assert isinstance(
        SampleApplicationModule,
        (ApplicationModuleDecorator, BaseModuleDecorator, ModuleDecorator),
    ), "SampleModule is not an instance of ModuleDecorator | BaseModuleDecorator"
    module_data = SampleApplicationModule.build()
    module_base = SampleApplicationModule.get_module()

    assert len(module_data.before_init) == 1
    assert len(module_data.after_init) == 1

    assert len(module_data.shutdown_event) == 1
    assert len(module_data.startup_event) == 1

    assert len(module_data.exception_handlers) == 1
    assert (
        module_data.exception_handlers.get(404).__name__
        == module_base.exception_404_override.__name__
    )

    assert len(module_data.middleware) == 1
    assert len(module_data.routes) == 4


def test_app_module_invalid_controller_and_router_parameter():
    injector = StarletteInjector()
    _type_app_module = ApplicationModuleDecorator(
        controllers=(type("SomeController", (), {}),)
    )(AppFactoryModule)

    with pytest.raises(
        ImproperConfiguration,
        match="Registered Controller is an invalid Controller Object",
    ):
        injector.container.install(_type_app_module)

    _type_app_module = ApplicationModuleDecorator(controllers=(mr,))(AppFactoryModule)

    with pytest.raises(
        ImproperConfiguration,
        match="Registered Controller is an invalid Controller Object",
    ):
        injector.container.install(_type_app_module)

    _type = ApplicationModuleDecorator(routers=(SampleController,))(AppFactoryModule)
    with pytest.raises(
        ImproperConfiguration, match="Registered Router is an invalid Router"
    ):
        injector.container.install(_type)

    _type_module = ModuleDecorator(routers=(SampleController,))(AppFactoryModule)
    _type_app_module = ApplicationModuleDecorator(modules=(_type_module,))(
        AppFactoryModule
    )
    with pytest.raises(
        ImproperConfiguration, match="Registered Router is an invalid Router"
    ):
        injector.container.install(_type_app_module)


def test_app_module_invalid_module_parameter():
    injector = StarletteInjector()
    _type_module = ModuleDecorator()
    _type_app_module = ApplicationModuleDecorator(modules=(_type_module,))(
        AppFactoryModule
    )
    with pytest.raises(
        ImproperConfiguration,
        match="ModuleDecorator is not used properly. It has to decorate a class",
    ):
        injector.container.install(_type_app_module)

    _type_app_module = ApplicationModuleDecorator(modules=(SampleController,))(
        AppFactoryModule
    )
    with pytest.raises(ImproperConfiguration, match="Object is an invalid Module type"):
        injector.container.install(_type_app_module)


def test_app_module_validation_exceptions():
    injector = StarletteInjector()

    _type_app_module = ApplicationModuleDecorator(modules=(SampleApplicationModule,))(
        AppFactoryModule
    )
    with pytest.raises(
        ImproperConfiguration,
        match="An app instance is entitled to one ApplicationModule",
    ):
        injector.container.install(_type_app_module)

    _type_app_module = ApplicationModuleDecorator()
    with pytest.raises(Exception, match="ModuleDecorator not properly configured"):
        injector.container.install(_type_app_module)

    with pytest.raises(
        ImproperConfiguration,
        match="ModuleDecorator is not used properly. It has to decorate a class",
    ):
        _type_app_module.validate_module_decorator()


def test_app_module_build_module_fails_for_invalid_type():
    injector = StarletteInjector()
    _type_app_module: ApplicationModuleDecorator = ApplicationModuleDecorator()(
        AppFactoryModule
    )
    with pytest.raises(
        ImproperConfiguration,
        match="Module can not be installed",
    ):
        _type_app_module.build_module(injector.container, type("InvalidModule", (), {}))

    with pytest.raises(
        ImproperConfiguration,
        match="An app instance is entitled to one ApplicationModule",
    ):
        _type_app_module.build_module(injector.container, SampleApplicationModule)


def test_app_module_build_module_works_for_valid_type():
    injector = StarletteInjector()
    _type_app_module: ApplicationModuleDecorator = ApplicationModuleDecorator()(
        AppFactoryModule
    )
    _type_app_module.build()
    assert len(_type_app_module.templating_modules) == 1
    module_instance, module_data = _type_app_module.build_module(
        injector.container, SampleModule
    )
    assert isinstance(module_instance, ModuleBase)
    assert isinstance(module_data, ModuleData)
    assert len(_type_app_module.templating_modules) == 2


def test_app_module_build_module_works_for_module_base_type():
    injector = StarletteInjector()
    _type_app_module: ApplicationModuleDecorator = ApplicationModuleDecorator()(
        AppFactoryModule
    )
    _type_app_module.build()
    assert len(_type_app_module.templating_modules) == 1
    module_instance, module_data = _type_app_module.build_module(
        injector.container, ModuleBaseExample
    )
    assert isinstance(module_instance, ModuleBase)
    assert isinstance(module_data, ModuleData)
    assert len(_type_app_module.templating_modules) == 1


def test_app_module_build_module_works_for_valid_existing_type_returns_default():
    injector = StarletteInjector()
    _type_app_module: ApplicationModuleDecorator = ApplicationModuleDecorator(
        modules=[SampleModule]
    )(AppFactoryModule)
    _type_app_module.build()
    assert len(_type_app_module.templating_modules) == 2
    module_instance, module_data = _type_app_module.build_module(
        injector.container, SampleModule
    )
    assert isinstance(module_instance, ModuleBase)
    assert isinstance(module_data, ModuleData)
    assert ModuleDecoratorBuilder.default() == module_data
    assert len(_type_app_module.templating_modules) == 2
