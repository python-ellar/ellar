import pytest
from starlette.routing import Route

from ellar.common import Module
from ellar.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_METADATA,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core import AppFactory, Config, ModuleBase
from ellar.core.modules.ref import (
    ModulePlainRef,
    ModuleProvider,
    ModuleTemplateRef,
    create_module_ref_factor,
)
from ellar.di import EllarInjector, TransientScope, injectable
from ellar.helper import get_name
from ellar.reflect import reflect

from .sample import (
    AnotherUserService,
    ModuleBaseExample,
    ModuleBaseExample2,
    SampleController,
    UserService,
)


@injectable(scope=TransientScope)
@Module()
class ModuleProviderTest(ModuleBase):
    def __init__(self, a: ModuleBaseExample, c: str = "C", d: float = 12.3):
        self.a = a
        self.c = c
        self.d = d


class InitKwargsModule(ModuleBase):
    def __init__(self, a: str, b: int, c: str = "C", d: float = 12.3):
        self.c = c
        self.d = d
        self.a = a
        self.b = b


def test_create_module_ref_factor_creates_right_module_ref():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    module_ref = create_module_ref_factor(
        ModuleBaseExample, config=config, container=container, a="a", b="b"
    )
    assert isinstance(module_ref, ModulePlainRef)
    assert module_ref._init_kwargs == dict(a="a", b="b")

    module_ref = create_module_ref_factor(
        ModuleBaseExample2, config=config, container=container
    )
    assert isinstance(module_ref, ModuleTemplateRef)
    assert module_ref._init_kwargs == dict()


def test_module_init_kwargs_build_correctly():
    config = Config()
    container = EllarInjector(auto_bind=False).container
    module_ref = create_module_ref_factor(
        InitKwargsModule, config=config, container=container
    )
    assert module_ref
    assert module_ref._init_kwargs == dict(d=12.3, c="C")


def test_module_ref_registers_module_type():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    with pytest.raises(Exception):
        container.injector.get(ModuleBaseExample)

    create_module_ref_factor(ModuleBaseExample, config=config, container=container)
    create_module_ref_factor(ModuleProviderTest, config=config, container=container)

    instance = container.injector.get(ModuleBaseExample)
    instance2 = container.injector.get(ModuleProviderTest)

    module_provider_module_base_example = container.get_binding(ModuleBaseExample)
    module_provider_module_provider_test = container.get_binding(ModuleProviderTest)

    assert isinstance(module_provider_module_base_example[0].provider, ModuleProvider)
    assert isinstance(module_provider_module_provider_test[0].provider, ModuleProvider)

    assert isinstance(instance, ModuleBaseExample)
    assert instance2.a is instance
    assert isinstance(instance2, ModuleProviderTest)
    assert instance2 is not container.injector.get(ModuleProviderTest)


def test_module_template_ref_template_filters():
    config = Config(**{TEMPLATE_GLOBAL_KEY: []})
    container = EllarInjector(auto_bind=False).container

    template_filter = config[TEMPLATE_FILTER_KEY]
    template_global_filter = config[TEMPLATE_GLOBAL_KEY]

    assert "some_template_global" not in template_global_filter
    assert "some_template_filter" not in template_filter

    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    template_filter = config[TEMPLATE_FILTER_KEY]
    template_global_filter = config[TEMPLATE_GLOBAL_KEY]

    assert isinstance(template_filter, dict) and isinstance(
        template_global_filter, dict
    )
    assert "some_template_global" in template_global_filter
    assert "some_template_filter" in template_filter

    config.update(**{TEMPLATE_GLOBAL_KEY: (), TEMPLATE_FILTER_KEY: set()})
    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    template_filter = config[TEMPLATE_FILTER_KEY]
    template_global_filter = config[TEMPLATE_GLOBAL_KEY]

    assert isinstance(template_filter, dict) and isinstance(
        template_global_filter, dict
    )
    assert "some_template_global" in template_global_filter
    assert "some_template_filter" in template_filter


def test_module_template_ref_scan_request_events():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    request_startup = config[ON_REQUEST_STARTUP_KEY]
    request_shutdown = config[ON_REQUEST_SHUTDOWN_KEY]

    assert len(request_startup) == 0 and len(request_shutdown) == 0

    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    request_startup = config[ON_REQUEST_STARTUP_KEY]
    request_shutdown = config[ON_REQUEST_SHUTDOWN_KEY]

    assert isinstance(request_startup, list) and isinstance(request_shutdown, list)
    assert "on_startup_handler" == get_name(request_startup[0])
    assert "on_shutdown_handler" == get_name(request_shutdown[0])

    config.update(**{ON_REQUEST_STARTUP_KEY: ()})
    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    request_startup = config[ON_REQUEST_STARTUP_KEY]
    request_shutdown = config[ON_REQUEST_SHUTDOWN_KEY]

    assert isinstance(request_startup, list) and isinstance(request_shutdown, list)
    assert "on_startup_handler" == get_name(request_startup[0])
    assert "on_shutdown_handler" == get_name(request_shutdown[0])


def test_module_template_ref_scan_exceptions_handlers():
    config = Config(**{EXCEPTION_HANDLERS_KEY: []})
    container = EllarInjector(auto_bind=False).container
    assert 404 not in config[EXCEPTION_HANDLERS_KEY]

    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    exception_handlers = config[EXCEPTION_HANDLERS_KEY]

    assert isinstance(exception_handlers, dict)
    assert 404 in exception_handlers


def test_module_template_ref_scan_middle_ware():
    config = Config(**{MIDDLEWARE_HANDLERS_KEY: ()})
    container = EllarInjector(auto_bind=False).container
    assert len(config[MIDDLEWARE_HANDLERS_KEY]) == 0

    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    middleware = config[MIDDLEWARE_HANDLERS_KEY]

    assert isinstance(middleware, list)
    assert "middleware" == get_name(middleware[0].options["dispatch"])

    config.update(**{MIDDLEWARE_HANDLERS_KEY: ()})
    create_module_ref_factor(ModuleBaseExample2, config=config, container=container)
    middleware = config[MIDDLEWARE_HANDLERS_KEY]

    assert isinstance(middleware, list)
    assert "middleware" == get_name(middleware[0].options["dispatch"])


def test_module_template_ref_get_all_routers():
    some_invalid_router = type("SomeInvalidRouter", (), {})
    config = Config()
    container = EllarInjector(auto_bind=False).container
    with reflect.context():
        reflect.define_metadata(
            MODULE_METADATA.ROUTERS,
            [
                some_invalid_router(),
                Route("/", endpoint=lambda request: "Test"),
                Route("/test", endpoint=lambda request: "Test"),
            ],
            ModuleBaseExample2,
        )
        module_ref = create_module_ref_factor(
            ModuleBaseExample2, config=config, container=container
        )
    assert len(module_ref.routers) == 5


def test_module_template_ref_get_all_routers_fails_for_invalid_controller():
    some_invalid_controller = type("SomeInvalidController", (), {})
    with reflect.context():
        reflect.define_metadata(
            MODULE_METADATA.CONTROLLERS, some_invalid_controller, ModuleBaseExample2
        )
        config = Config()
        container = EllarInjector(auto_bind=False).container

        with pytest.raises(AssertionError, match="Invalid Controller Type."):
            create_module_ref_factor(
                ModuleBaseExample2, config=config, container=container
            )


def test_module_plain_ref_routes_return_empty_list():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    module_ref = create_module_ref_factor(
        ModuleBaseExample, config=config, container=container
    )
    assert module_ref.routes == []


def test_module_template_ref_routes_returns_valid_routes():
    some_invalid_router = type("SomeInvalidRouter2", (), {})
    config = Config()
    container = EllarInjector(auto_bind=False).container
    with reflect.context():
        reflect.define_metadata(
            MODULE_METADATA.ROUTERS,
            [some_invalid_router(), Route("/", endpoint=lambda request: "Test")],
            ModuleBaseExample2,
        )
        module_ref = create_module_ref_factor(
            ModuleBaseExample2, config=config, container=container
        )
    assert len(module_ref.routers) == 4
    assert len(module_ref.routes) == 5


def test_module_template_ref_routes():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    module_ref = create_module_ref_factor(
        ModuleBaseExample2, config=config, container=container
    )
    assert len(module_ref.routers) == 2
    counts = sum(len(item.routes) for item in module_ref.routers)
    assert len(module_ref.routes) == counts


def test_module_template_registers_providers_and_controllers():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    with pytest.raises(Exception):
        container.injector.get(UserService)

    with pytest.raises(Exception):
        container.injector.get(AnotherUserService)

    with pytest.raises(Exception):
        container.injector.get(SampleController)

    module_ref = create_module_ref_factor(
        ModuleBaseExample2, config=config, container=container
    )
    module_ref.run_module_register_services()

    assert isinstance(container.injector.get(UserService), UserService)
    assert isinstance(container.injector.get(AnotherUserService), AnotherUserService)
    assert isinstance(container.injector.get(SampleController), SampleController)


def test_run_application_ready_works():
    test_module_init_calls = type("TestModuleInitCalls", (ModuleBaseExample,), {})
    Module()(test_module_init_calls)
    app = AppFactory.create_app()

    module_ref = create_module_ref_factor(
        test_module_init_calls, config=app.config, container=app.injector.container
    )
    assert test_module_init_calls._before_init_called is False
    module_ref.run_module_register_services()
    assert test_module_init_calls._before_init_called

    assert test_module_init_calls._app_ready_called is False
    module_ref.run_application_ready(app)
    assert test_module_init_calls._app_ready_called
