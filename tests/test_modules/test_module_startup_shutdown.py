from ellar.common import IApplicationShutdown, IApplicationStartup, Module, ModuleRouter
from ellar.reflect import asynccontextmanager
from ellar.testing import Test

router = ModuleRouter("")


@router.get("/home")
def home():
    return "Works"


@Module(routers=[router])
class OnStartupModule(IApplicationStartup):
    def __init__(self):
        self.on_startup_called = False

    async def on_startup(self, app) -> None:
        self.on_startup_called = True


@Module()
class OnShutdownModule(IApplicationShutdown):
    def __init__(self):
        self.on_shutdown_called = False

    async def on_shutdown(self) -> None:
        self.on_shutdown_called = True


@asynccontextmanager
async def _testing_life_span(app):
    yield {"life_span_testing": "Ellar"}


tm = Test.create_test_module(
    modules=[OnShutdownModule, OnStartupModule],
    config_module={"DEFAULT_LIFESPAN_HANDLER": _testing_life_span},
)


def test_on_startup_and_on_shutdown_works():
    client = tm.get_test_client()
    on_shutdown_module_instance = tm.get(OnShutdownModule)
    on_startup_module_instance = tm.get(OnStartupModule)

    assert on_startup_module_instance.on_startup_called is False
    assert on_shutdown_module_instance.on_shutdown_called is False

    with client:
        res = client.get("/home")
        assert res.status_code == 200
        assert res.text == '"Works"'

        assert on_startup_module_instance.on_startup_called

    assert on_shutdown_module_instance.on_shutdown_called
