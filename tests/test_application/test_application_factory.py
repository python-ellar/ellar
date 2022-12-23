from starlette.routing import Host, Mount

from ellar.common import Module
from ellar.core import AppFactory, Config, ModuleBase, TestClient
from ellar.di import EllarInjector

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
    modules_dict = AppFactory.read_all_module(module=BModule)
    assert len(modules_dict) == 2
    assert list(modules_dict.values())[0] is AModule
    assert list(modules_dict.values())[1] is ApplicationModule

    modules_list = AppFactory.get_all_modules(module=AModule)
    assert len(modules_list) == 2
    assert modules_list[0] is AModule
    assert modules_list[1] is ApplicationModule

    modules_dict = AppFactory.read_all_module(module=ApplicationModule)
    assert len(modules_dict) == 0


def test_factory__build_modules():
    config = Config()
    injector = EllarInjector()
    assert len(injector.get_modules()) == 0

    AppFactory._build_modules(app_module=BModule, config=config, injector=injector)
    module_refs = injector.get_modules()
    assert len(module_refs) == 3

    modules = [AModule, ApplicationModule, BModule]
    for k, v in module_refs.items():
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
    assert isinstance(module_instance, ModuleBase)
    assert "ellar.core.factory.Module" in str(module_instance.__class__)


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
