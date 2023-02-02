import pytest
from starlette.routing import Route

from ellar.common import (
    Module,
    exception_handler,
    middleware,
    on_shutdown,
    on_startup,
    template_filter,
    template_global,
)
from ellar.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_METADATA,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core import AppFactory, Config, ModuleBase, TestClientFactory
from ellar.core.modules.ref import (
    InvalidModuleTypeException,
    ModulePlainRef,
    ModuleProvider,
    ModuleTemplateRef,
    create_module_ref_factor,
)
from ellar.di import EllarInjector, TransientScope, injectable
from ellar.helper import get_name
from ellar.reflect import reflect

from .sample import AnotherUserService, ModuleBaseExample, SampleController, UserService


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


class NonTemplateModuleExample(ModuleBase):
    def __init__(self, a, b):
        self.a = a
        self.b = b


def test_create_module_ref_factor_creates_right_module_ref():

    config = Config()
    container = EllarInjector(auto_bind=False).container

    module_ref = create_module_ref_factor(
        NonTemplateModuleExample, config=config, container=container, a="a", b="b"
    )
    assert isinstance(module_ref, ModulePlainRef)
    assert module_ref._init_kwargs == dict(a="a", b="b")

    module_ref = create_module_ref_factor(
        ModuleBaseExample, config=config, container=container
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
    @Module()
    class ModuleTemplateExample(ModuleBase):
        @template_global()
        def some_template_global(cls, n):
            pass

        @template_filter()
        def some_template_filter(cls, n):
            pass

    config = Config(**{TEMPLATE_GLOBAL_KEY: []})
    container = EllarInjector(auto_bind=False).container

    template_filter_functions = config[TEMPLATE_FILTER_KEY]
    template_global_filter_functions = config[TEMPLATE_GLOBAL_KEY]

    assert "some_template_global" not in template_global_filter_functions
    assert "some_template_filter" not in template_filter_functions

    create_module_ref_factor(ModuleTemplateExample, config=config, container=container)
    template_filter_functions = config[TEMPLATE_FILTER_KEY]
    template_global_filter_functions = config[TEMPLATE_GLOBAL_KEY]

    assert isinstance(template_filter_functions, dict) and isinstance(
        template_global_filter_functions, dict
    )
    assert "some_template_global" in template_global_filter_functions
    assert "some_template_filter" in template_filter_functions


def test_module_template_ref_scan_starlette_app_events():
    @Module()
    class RouterEventsModuleExample:
        @on_startup
        async def on_startup_handler(cls):
            pass

        @on_shutdown
        def on_shutdown_handler(cls):
            pass

    config = Config()
    container = EllarInjector(auto_bind=False).container

    request_startup = config[ON_REQUEST_STARTUP_KEY]
    request_shutdown = config[ON_REQUEST_SHUTDOWN_KEY]

    assert len(request_startup) == 0 and len(request_shutdown) == 0

    create_module_ref_factor(
        RouterEventsModuleExample, config=config, container=container
    )
    request_startup = config[ON_REQUEST_STARTUP_KEY]
    request_shutdown = config[ON_REQUEST_SHUTDOWN_KEY]

    assert isinstance(request_startup, list) and isinstance(request_shutdown, list)
    assert "on_startup_handler" == get_name(request_startup[0].handler)
    assert "on_shutdown_handler" == get_name(request_shutdown[0].handler)


def test_module_template_ref_scan_exceptions_handlers():
    @Module()
    class ModuleExceptionHandlerSample(ModuleBase):
        @exception_handler(404)
        async def exception_404(cls, ctx, exc):
            pass

    config = Config(**{EXCEPTION_HANDLERS_KEY: []})
    container = EllarInjector(auto_bind=False).container
    assert 404 not in config[EXCEPTION_HANDLERS_KEY]

    create_module_ref_factor(
        ModuleExceptionHandlerSample, config=config, container=container
    )
    exception_handlers = config[EXCEPTION_HANDLERS_KEY]

    assert isinstance(exception_handlers, list)
    handler = exception_handlers[0]
    k, v = iter(handler)
    assert 404 == k


def test_module_template_ref_scan_middle_ware():
    @Module()
    class ModuleMiddlewareExample(ModuleBase):
        @middleware()
        async def middleware_func(cls, context, call_next):
            await call_next()

    config = Config(**{MIDDLEWARE_HANDLERS_KEY: ()})
    container = EllarInjector(auto_bind=False).container
    assert len(config[MIDDLEWARE_HANDLERS_KEY]) == 0

    create_module_ref_factor(
        ModuleMiddlewareExample, config=config, container=container
    )
    config_middleware = config[MIDDLEWARE_HANDLERS_KEY]

    assert isinstance(config_middleware, list)
    assert "middleware_func" == get_name(config_middleware[0].options["dispatch"])


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
            ModuleBaseExample,
        )
        module_ref = create_module_ref_factor(
            ModuleBaseExample, config=config, container=container
        )
    assert len(module_ref.routers) == 5


def test_module_template_ref_get_all_routers_fails_for_invalid_controller():
    some_invalid_controller = type("SomeInvalidController", (), {})
    with reflect.context():
        reflect.define_metadata(
            MODULE_METADATA.CONTROLLERS, [some_invalid_controller], ModuleBaseExample
        )
        config = Config()
        container = EllarInjector(auto_bind=False).container

        with pytest.raises(AssertionError, match="Invalid Controller Type."):
            create_module_ref_factor(
                ModuleBaseExample, config=config, container=container
            )


def test_invalid_module_template_ref():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    invalid_module = type("InvalidModule", (), {})
    with pytest.raises(
        InvalidModuleTypeException,
        match="must be a subclass of `ellar.core.ModuleBase`",
    ):
        create_module_ref_factor(invalid_module, config=config, container=container)


def test_module_plain_ref_routes_return_empty_list():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    module_ref = create_module_ref_factor(
        NonTemplateModuleExample, config=config, container=container
    )
    assert module_ref.routes == []
    assert isinstance(module_ref.config, Config)


def test_module_template_ref_routes_returns_valid_routes():
    some_invalid_router = type("SomeInvalidRouter2", (), {})
    config = Config()
    container = EllarInjector(auto_bind=False).container
    with reflect.context():
        reflect.define_metadata(
            MODULE_METADATA.ROUTERS,
            [some_invalid_router(), Route("/", endpoint=lambda request: "Test")],
            ModuleBaseExample,
        )
        module_ref = create_module_ref_factor(
            ModuleBaseExample, config=config, container=container
        )
    assert len(module_ref.routers) == 4
    assert len(module_ref.routes) == 3


def test_module_template_ref_routes():
    config = Config()
    container = EllarInjector(auto_bind=False).container

    module_ref = create_module_ref_factor(
        ModuleBaseExample, config=config, container=container
    )
    assert len(module_ref.routers) == 2
    counts = sum(len(item.routes) for item in module_ref.routers)
    assert counts == 4


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
        ModuleBaseExample, config=config, container=container
    )
    module_ref.run_module_register_services()

    assert isinstance(container.injector.get(UserService), UserService)
    assert isinstance(container.injector.get(AnotherUserService), AnotherUserService)
    assert isinstance(container.injector.get(SampleController), SampleController)


def test_run_application_ready_works():
    @Module()
    class TestModuleCycleExample(ModuleBase):
        _before_init_called = False
        _app_ready_called = False

        @classmethod
        def before_init(cls, config: Config) -> None:
            cls._before_init_called = True

        def application_ready(self, app) -> None:
            self.__class__._app_ready_called = True

    assert TestModuleCycleExample._before_init_called is False
    assert TestModuleCycleExample._app_ready_called is False

    AppFactory.create_from_app_module(TestModuleCycleExample)

    assert TestModuleCycleExample._before_init_called
    assert TestModuleCycleExample._app_ready_called


def test_module_request_events():
    @Module()
    class RouterEventsModuleExample:
        _on_shutdown_handler_called = False
        _on_startup_handler_called = False

        @on_startup
        async def on_startup_handler(cls):
            cls._on_startup_handler_called = True

        @on_shutdown
        def on_shutdown_handler(cls):
            cls._on_shutdown_handler_called = True

    assert RouterEventsModuleExample._on_shutdown_handler_called is False
    assert RouterEventsModuleExample._on_startup_handler_called is False

    tm = TestClientFactory.create_test_module_from_module(RouterEventsModuleExample)

    test_client = tm.get_client()
    with test_client as client:
        client.get("/")

    assert RouterEventsModuleExample._on_shutdown_handler_called
    assert RouterEventsModuleExample._on_startup_handler_called
