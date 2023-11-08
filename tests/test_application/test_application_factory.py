import pytest
from ellar.app import AppFactory
from ellar.common import Module
from ellar.common.constants import MODULE_WATERMARK
from ellar.core import Config, ModuleBase, ModuleSetup
from ellar.di import EllarInjector
from ellar.reflect import reflect
from ellar.testing import TestClient
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
    modules_dict = AppFactory.read_all_module(ModuleSetup(BModule))
    assert len(modules_dict) == 2
    assert list(modules_dict.values())[0].module is AModule
    assert list(modules_dict.values())[1].module is ApplicationModule

    modules_list = AppFactory.get_all_modules(ModuleSetup(AModule))
    assert len(modules_list) == 2
    assert modules_list[0].module is AModule
    assert modules_list[1].module is ApplicationModule

    modules_dict = AppFactory.read_all_module(ModuleSetup(ApplicationModule))
    assert len(modules_dict) == 0


def test_factory__build_modules():
    config = Config()
    injector = EllarInjector()
    assert len(injector.get_modules()) == 0

    AppFactory._build_modules(app_module=BModule, config=config, injector=injector)
    module_refs = injector.get_modules()
    assert len(module_refs) == 3

    modules = [AModule, ApplicationModule, BModule]
    for k, _v in module_refs.items():
        assert k in modules


def test_factory_create_from_app_module():
    app = AppFactory.create_from_app_module(
        module=BModule,
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
    first_module_ref = next(app.get_module_loaders())
    module_instance = first_module_ref.get_module_instance()
    assert not isinstance(module_instance, ModuleBase)
    assert reflect.get_metadata(MODULE_WATERMARK, type(module_instance))
    assert "ellar.app.factory.Module" in str(module_instance.__class__)


def test_factory_create_app_works(tmpdir):
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

    template = app.jinja_environment.get_template("example.html")
    result = template.render()
    assert result == "<html>Hello World<html/>"


def test_invalid_config_module_raise_exception():
    with pytest.raises(Exception) as ex:
        AppFactory.create_app(config_module=set())

    assert str(ex.value) == "config_module should be a importable str or a dict object"
