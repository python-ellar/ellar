import re

from ellar.auth.session import ISessionStrategy
from ellar.auth.session.strategy import SessionClientStrategy
from ellar.common import Controller, Inject, delete, get, post
from ellar.core import Request
from ellar.core.routing import ControllerRouterFactory
from ellar.testing import Test
from starlette.routing import Mount


@Controller("/")
class SessionSampleController:
    @get()
    def view_session(self, request: Inject[Request]):
        return {"session": request.session}

    @post()
    async def update_session(self, request: Inject[Request]):
        data = await request.json()
        request.session.update(data)
        return {"session": request.session}

    @delete()
    async def clear_session(self, request: Inject[Request]):
        request.session.clear()
        return {"session": request.session}


def test_session():
    test_module = Test.create_test_module(
        controllers=[SessionSampleController], config_module={"SECRET_KEY": "secret"}
    )
    test_module.override_provider(ISessionStrategy, use_class=SessionClientStrategy)
    client = test_module.get_test_client()

    response = client.get("/")
    assert response.json() == {"session": {}}

    response = client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    max_age_matches = re.search(r"; Max-Age=([0-9]+);", set_cookie)
    assert max_age_matches is not None
    assert int(max_age_matches[1]) == 14 * 24 * 3600

    response = client.get("/")
    assert response.json() == {"session": {"some": "data"}}

    response = client.delete("/")
    assert response.json() == {"session": {}}

    response = client.get("/")
    assert response.json() == {"session": {}}


def test_session_expires():
    test_module = Test.create_test_module(
        controllers=[SessionSampleController],
        config_module={"SECRET_KEY": "secret", "SESSION_COOKIE_MAX_AGE": -1},
    )
    test_module.override_provider(ISessionStrategy, use_class=SessionClientStrategy)
    client = test_module.get_test_client()

    response = client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # requests removes expired cookies from response.cookies, we need to
    # fetch session id from the headers and pass it explicitly
    expired_cookie_header = response.headers["set-cookie"]
    expired_session_match = re.search(r"session=([^;]*);", expired_cookie_header)
    assert expired_session_match is not None
    expired_session_value = expired_session_match[1]
    client = test_module.get_test_client(cookies={"session": expired_session_value})
    response = client.get("/")
    assert response.json() == {"session": {}}


def test_secure_session():
    test_module = Test.create_test_module(
        controllers=[SessionSampleController],
        config_module={"SECRET_KEY": "secret", "SESSION_COOKIE_SECURE": True},
    )
    test_module.override_provider(ISessionStrategy, use_class=SessionClientStrategy)
    secure_client = test_module.get_test_client(base_url="https://testserver")
    unsecure_client = test_module.get_test_client(base_url="http://testserver")

    response = unsecure_client.get("/")
    assert response.json() == {"session": {}}

    response = unsecure_client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    response = unsecure_client.get("/")
    assert response.json() == {"session": {}}

    response = secure_client.get("/")
    assert response.json() == {"session": {}}

    response = secure_client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    response = secure_client.get("/")
    assert response.json() == {"session": {"some": "data"}}

    response = secure_client.delete("/")
    assert response.json() == {"session": {}}

    response = secure_client.get("/")
    assert response.json() == {"session": {}}


def test_session_cookie_sub_path():
    test_module = Test.create_test_module(
        controllers=[SessionSampleController],
        routers=[
            Mount(
                "/second_app",
                app=ControllerRouterFactory.build(SessionSampleController),
            )
        ],
        config_module={"SECRET_KEY": "secret", "SESSION_COOKIE_PATH": "/second_app"},
    )
    test_module.override_provider(ISessionStrategy, use_class=SessionClientStrategy)

    client_second_app = test_module.get_test_client(
        base_url="http://testserver/second_app"
    )
    client = test_module.get_test_client(base_url="http://testserver/")

    response = client_second_app.post("/second_app/", json={"some": "data"})
    assert response.status_code == 200

    cookie = response.headers["set-cookie"]
    cookie_path_match = re.search(r"; path=(\S+);", cookie)
    assert cookie_path_match is not None

    cookie_path = cookie_path_match.groups()[0]
    assert cookie_path == "/second_app"

    response = client_second_app.get("/second_app/")
    assert response.json() == {"session": {"some": "data"}}

    response = client.post("/", json={"some": "data"})
    assert response.status_code == 200
    assert response.json() == {"session": {"some": "data"}}

    response = client.get("/")
    assert response.json() == {"session": {}}


def test_invalid_session_cookie():
    test_module = Test.create_test_module(
        controllers=[SessionSampleController], config_module={"SECRET_KEY": "secret"}
    )
    test_module.override_provider(ISessionStrategy, use_class=SessionClientStrategy)
    client = test_module.get_test_client()

    response = client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # we expect it to not raise an exception if we provide a bogus session cookie
    client = test_module.get_test_client(cookies={"session": "invalid"})
    response = client.get("/")
    assert response.json() == {"session": {}}


def test_session_cookie():
    test_module = Test.create_test_module(
        controllers=[SessionSampleController],
        config_module={"SECRET_KEY": "secret", "SESSION_COOKIE_MAX_AGE": None},
    )
    test_module.override_provider(ISessionStrategy, use_class=SessionClientStrategy)
    client = test_module.get_test_client()

    response = client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    assert "Max-Age" not in set_cookie

    client.cookies.delete("session")
    response = client.get("/")
    assert response.json() == {"session": {}}
