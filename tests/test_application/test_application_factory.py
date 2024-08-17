import pytest
from ellar.app import AppFactory
from ellar.common import Module
from ellar.common.constants import MODULE_WATERMARK
from ellar.common.exceptions import ImproperConfiguration
from ellar.core import LazyModuleImport as lazyLoad
from ellar.core import ModuleBase, ModuleSetup, injector_context
from ellar.di import ProviderConfig
from ellar.reflect import reflect
from ellar.testing import TestClient
from ellar.utils import get_unique_type
from jinja2 import Environment
from starlette.routing import Host, Mount

from .sample import (
    AppAPIKey,
    ApplicationModule,
    ClassBaseController,
    create_tmp_template_and_static_dir,
    router,
    sub_domain,
    users,
)


@Module(modules=[ApplicationModule])
class AModule:
    pass


@Module(modules=(AModule,))
class BModule:
    pass


def test_factory__read_all_module():
    modules_tree_manager = AppFactory.read_all_module(ModuleSetup(BModule))
    dependencies = modules_tree_manager.get_module_dependencies(BModule)
    assert len(dependencies) == 1
    assert dependencies[0].value.module == AModule

    a_dependencies = modules_tree_manager.get_module_dependencies(AModule)
    assert len(a_dependencies) == 1
    assert a_dependencies[0].value.module is ApplicationModule

    c_dependencies = modules_tree_manager.get_module_dependencies(ApplicationModule)
    assert len(c_dependencies) == 0


def test_factory_create_from_app_module():
    app = AppFactory.create_from_app_module(
        module=lazyLoad("tests.test_application.test_application_factory:BModule"),
        global_guards=[AppAPIKey],
        config_module="tests.test_application.config:ConfigTrustHostConfigure",
    )
    assert app.get_guards() == [AppAPIKey]
    assert (
        app.config.config_module
        == "tests.test_application.config:ConfigTrustHostConfigure"
    )


def test_factory_create_app_dynamically_creates_module():
    app = AppFactory.create_app()
    first_module_ref = app.injector.tree_manager.get_app_module()
    module_instance = first_module_ref.get_module_instance()
    assert not isinstance(module_instance, ModuleBase)
    assert reflect.get_metadata(MODULE_WATERMARK, type(module_instance))
    assert "ellar.utils.DynamicType" in str(module_instance.__class__)


async def test_factory_create_app_works(tmpdir, anyio_backend):
    create_tmp_template_and_static_dir(tmpdir)

    @Module()
    class CModule:
        pass

    app = AppFactory.create_app(
        modules=(CModule,),
        global_guards=[AppAPIKey],
        config_module="tests.test_application.config:ConfigTrustHostConfigure",
        controllers=(ClassBaseController,),
        routers=[
            Host("{subdomain}.example.org", app=sub_domain),
            Mount("/users", app=users),
            router,
        ],
        template_folder="templates",
        static_folder="statics",
        base_directory=tmpdir,
    )

    client = TestClient(app)
    res = client.get("/static/example.txt")
    assert res.status_code == 200
    assert res.text == "<file content>"
    async with injector_context(app.injector):
        template = app.injector.get(Environment).get_template("example.html")
        result = template.render()
        assert result == "<html>Hello World<html/>"


def test_invalid_config_module_raise_exception():
    with pytest.raises(Exception) as ex:
        AppFactory.create_app(config_module=set())

    assert str(ex.value) == "config_module should be a importable str or a dict object"


def test_config_overrider_core_service_registration():
    provider_type = get_unique_type()
    with pytest.raises(
        ImproperConfiguration,
        match=f"There is not core service identify as {provider_type}",
    ):
        AppFactory.create_app(
            config_module={"OVERRIDE_CORE_SERVICE": [ProviderConfig(provider_type)]}
        )
