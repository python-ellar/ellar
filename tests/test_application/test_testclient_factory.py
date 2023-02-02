from abc import abstractmethod

from starlette.routing import Host, Mount

from ellar.constants import MODULE_METADATA
from ellar.core import TestClientFactory
from ellar.di import ProviderConfig
from ellar.reflect import reflect

from .sample import (
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
    tm = TestClientFactory.create_test_module(
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

    client = tm.get_client()
    res = client.get("/static/example.txt")
    assert res.status_code == 200
    assert res.text == "<file content>"

    template = tm.app.jinja_environment.get_template("example.html")
    result = template.render()
    assert result == "<html>Hello World<html/>"

    client = tm.get_client(base_url="https://foo.example.org/")

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

    tm = TestClientFactory.create_test_module_from_module(
        module=ApplicationModule,
        mock_providers=(
            ProviderConfig(
                base_type=IFoo, use_value=MockFoo()
            ),  # force provider override
        ),
    )

    client = tm.get_client(base_url="https://foo.example.org/")

    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Subdomain: foo"

    ifoo: IFoo = tm.app.injector.get(IFoo)
    assert isinstance(ifoo, MockFoo)
