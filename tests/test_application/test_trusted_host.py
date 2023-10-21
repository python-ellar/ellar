from ellar.common import Inject, get
from ellar.testing import Test
from starlette.requests import Request
from starlette.responses import PlainTextResponse


def test_trusted_host_middleware(test_client_factory):
    @get()
    def homepage(request: Inject[Request]):
        return PlainTextResponse("OK", status_code=200)

    tm = Test.create_test_module(
        config_module={"ALLOWED_HOSTS": ["testserver", "*.testserver"]}
    )
    app = tm.create_application()
    app.router.append(homepage)

    assert app.debug is False

    client = tm.get_test_client()

    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_test_client(base_url="http://subdomain.testserver")
    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_test_client(base_url="http://invalidhost")
    response = client.get("/")
    assert response.status_code == 400


def test_trusted_host_middleware_works_for_debug_true(test_client_factory):
    @get()
    def homepage(request: Inject[Request]):
        return PlainTextResponse("OK", status_code=200)

    tm = Test.create_test_module(
        config_module={"ALLOWED_HOSTS": ["testserver", "*.testserver"]}
    )
    app = tm.create_application()
    app.router.append(homepage)

    assert app.debug is False
    app.debug = True

    client = tm.get_test_client()

    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_test_client(base_url="http://subdomain.testserver")
    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_test_client(base_url="http://invalidhost")
    response = client.get("/")
    assert response.status_code == 200


def test_default_allowed_hosts():
    tm = Test.create_test_module()
    assert tm.create_application().config.ALLOWED_HOSTS == ["*"]


def test_www_redirect(test_client_factory):
    @get()
    def homepage(request: Inject[Request]):
        return PlainTextResponse("OK", status_code=200)

    tm = Test.create_test_module(config_module={"ALLOWED_HOSTS": ["www.example.com"]})
    app = tm.create_application()
    app.router.append(homepage)

    client = tm.get_test_client(base_url="https://example.com")
    response = client.get("/")
    assert response.status_code == 200
    assert response.url == "https://www.example.com/"
