from starlette.requests import Request
from starlette.responses import PlainTextResponse

from ellar.common import get
from ellar.core import TestClientFactory


def test_trusted_host_middleware(test_client_factory):
    @get()
    def homepage(request: Request):
        return PlainTextResponse("OK", status_code=200)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    tm.app.config.ALLOWED_HOSTS = ["testserver", "*.testserver"]

    tm.app.rebuild_middleware_stack()
    assert tm.app.debug is False

    client = tm.get_client()

    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_client(base_url="http://subdomain.testserver")
    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_client(base_url="http://invalidhost")
    response = client.get("/")
    assert response.status_code == 400


def test_trusted_host_middleware_works_for_debug_true(test_client_factory):
    @get()
    def homepage(request: Request):
        return PlainTextResponse("OK", status_code=200)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)

    tm.app.config.ALLOWED_HOSTS = ["testserver", "*.testserver"]
    assert tm.app.debug is False
    tm.app.debug = True

    client = tm.get_client()

    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_client(base_url="http://subdomain.testserver")
    response = client.get("/")
    assert response.status_code == 200

    client = tm.get_client(base_url="http://invalidhost")
    response = client.get("/")
    assert response.status_code == 200


def test_default_allowed_hosts():
    tm = TestClientFactory.create_test_module()
    assert tm.app.config.ALLOWED_HOSTS == ["*"]


def test_www_redirect(test_client_factory):
    @get()
    def homepage(request: Request):
        return PlainTextResponse("OK", status_code=200)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)

    tm.app.config.ALLOWED_HOSTS = ["www.example.com"]

    tm.app.rebuild_middleware_stack()

    client = tm.get_client(base_url="https://example.com")
    response = client.get("/")
    assert response.status_code == 200
    assert response.url == "https://www.example.com/"
