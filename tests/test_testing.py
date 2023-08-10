from abc import abstractmethod

from ellar.common.constants import MODULE_METADATA
from ellar.di import ProviderConfig
from ellar.reflect import reflect
from ellar.testing import Test
from starlette.routing import Host, Mount

from .test_application.sample import (
    ApplicationModule,
    ClassBaseController,
    create_tmp_template_and_static_dir,
    router,
    sub_domain,
    users,
)


class IFoo:
    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_full_name(self):
        pass


class Foo(IFoo):
    def get_name(self):
        return "Ellar"

    def get_full_name(self):
        return "Ellar Python Framework"


class MockFoo(IFoo):
    def get_name(self):
        return "whatever name"

    def get_full_name(self):
        return "some full name"


def test_test_client_factory_create_test_module(tmpdir):
    create_tmp_template_and_static_dir(tmpdir)
    tm = Test.create_test_module(
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

    client = tm.get_test_client()
    res = client.get("/static/example.txt")
    assert res.status_code == 200
    assert res.text == "<file content>"

    template = tm.create_application().jinja_environment.get_template("example.html")
    result = template.render()
    assert result == "<html>Hello World<html/>"

    client = tm.get_test_client(base_url="https://foo.example.org/")

    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Subdomain: foo"


def test_client_factory_create_test_module_from_module():
    reflect.metadata(
        metadata_key=MODULE_METADATA.PROVIDERS,
        metadata_value=[ProviderConfig(base_type=IFoo, use_class=Foo)],
    )(
        ApplicationModule
    )  # dynamically add IFoo to ApplicationModule Providers

    tm = Test.create_test_module(
        modules=[ApplicationModule],
    ).override_provider(IFoo, use_value=MockFoo())

    client = tm.get_test_client(base_url="https://foo.example.org/")

    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Subdomain: foo"

    ifoo: IFoo = tm.get(IFoo)
    assert isinstance(ifoo, MockFoo)
