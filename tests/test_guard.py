import pytest
from ellar.common import APIException, Inject, UseGuards, get, serialize_object
from ellar.core import AppFactory, Reflector, Request
from ellar.core.guards import (
    GuardAPIKeyCookie,
    GuardAPIKeyHeader,
    GuardAPIKeyQuery,
    GuardHttpBasicAuth,
    GuardHttpBearerAuth,
    GuardHttpDigestAuth,
)
from ellar.di import injectable
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import TestClient
from starlette.status import HTTP_401_UNAUTHORIZED


class CustomException(APIException):
    pass


@injectable()
class QuerySecretKeyInjectable(GuardAPIKeyQuery):
    def __init__(self, reflector: Reflector) -> None:
        super().__init__()
        self.reflector = reflector

    async def authentication_handler(self, connection, key):
        if key == "querysecretkey":
            return key


class QuerySecretKey(GuardAPIKeyQuery):
    async def authentication_handler(self, connection, key):
        if key == "querysecretkey":
            return key


class HeaderSecretKey(GuardAPIKeyHeader):
    async def authentication_handler(self, connection, key):
        if key == "headersecretkey":
            return key


@injectable()
class HeaderSecretKeyCustomException(HeaderSecretKey):
    exception_class = CustomException


class CookieSecretKey(GuardAPIKeyCookie):
    openapi_name = "API Key Auth"

    async def authentication_handler(self, connection, key):
        if key == "cookiesecretkey":
            return key


class BasicAuth(GuardHttpBasicAuth):
    openapi_name = "API Authentication"

    async def authentication_handler(self, connection, credentials):
        if credentials.username == "admin" and credentials.password == "secret":
            return credentials.username


@injectable()
class BearerAuth(GuardHttpBearerAuth):
    openapi_name = "JWT Authentication"

    async def authentication_handler(self, connection, credentials):
        if credentials.credentials == "bearertoken":
            return credentials.credentials


@injectable()
class DigestAuth(GuardHttpDigestAuth):
    async def authentication_handler(self, connection, credentials):
        if credentials.credentials == "digesttoken":
            return credentials.credentials


app = AppFactory.create_app()


for _path, auth in [
    ("apikeyquery", QuerySecretKey()),
    ("apikeyquery-injectable", QuerySecretKeyInjectable),
    ("apikeyheader", HeaderSecretKey()),
    ("apikeycookie", CookieSecretKey()),
    ("basic", BasicAuth()),
    ("bearer", BearerAuth),
    ("digest", DigestAuth),
    ("customexception", HeaderSecretKeyCustomException),
]:

    @get(f"/{_path}")
    @UseGuards(auth)
    def auth_demo_endpoint(request: Inject[Request]):
        return {"authentication": request.user}

    app.router.append(auth_demo_endpoint)

client = TestClient(app)

BODY_UNAUTHORIZED_DEFAULT = {"detail": "Forbidden"}


@pytest.mark.parametrize(
    "path,kwargs,expected_code,expected_body",
    [
        ("/apikeyquery", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeyquery?key=querysecretkey",
            {},
            200,
            {"authentication": "querysecretkey"},
        ),
        (
            "/apikeyquery-injectable",
            {},
            HTTP_401_UNAUTHORIZED,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        (
            "/apikeyquery-injectable?key=querysecretkey",
            {},
            200,
            {"authentication": "querysecretkey"},
        ),
        ("/apikeyheader", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeyheader",
            {"headers": {"key": "headersecretkey"}},
            200,
            {"authentication": "headersecretkey"},
        ),
        ("/apikeycookie", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeycookie",
            {"cookies": {"key": "cookiesecretkey"}},
            200,
            {"authentication": "cookiesecretkey"},
        ),
        ("/basic", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/basic",
            {"headers": {"Authorization": "Basic YWRtaW46c2VjcmV0"}},
            200,
            {"authentication": "admin"},
        ),
        (
            "/basic",
            {"headers": {"Authorization": "Basic d2hhdGV2ZXI="}},
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        (
            "/basic",
            {"headers": {"Authorization": "YWRtaW46c2VjcmV0"}},
            200,
            {"authentication": "admin"},
        ),
        (
            "/basic",
            {"headers": {"Authorization": "Basic invalid"}},
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        (
            "/basic",
            {"headers": {"Authorization": "some invalid value"}},
            HTTP_401_UNAUTHORIZED,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        ("/bearer", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/bearer",
            {"headers": {"Authorization": "Bearer bearertoken"}},
            200,
            {"authentication": "bearertoken"},
        ),
        (
            "/bearer",
            {"headers": {"Authorization": "Invalid bearertoken"}},
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        ("/digest", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/digest",
            {"headers": {"Authorization": "Digest digesttoken"}},
            200,
            {"authentication": "digesttoken"},
        ),
        (
            "/digest",
            {"headers": {"Authorization": "Invalid digesttoken"}},
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        ("/customexception", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/customexception",
            {"headers": {"key": "headersecretkey"}},
            200,
            {"authentication": "headersecretkey"},
        ),
    ],
)
def test_auth(path, kwargs, expected_code, expected_body):
    response = client.get(path, **kwargs)
    assert response.status_code == expected_code
    assert response.json() == expected_body


def test_auth_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document["components"]["securitySchemes"] == {
        "API Key Auth": {"type": "apiKey", "in": "cookie", "name": "key"},
        "HeaderSecretKey": {
            "type": "apiKey",
            "in": "header",
            "name": "key",
        },
        "QuerySecretKey": {"type": "apiKey", "in": "query", "name": "key"},
        "QuerySecretKeyInjectable": {
            "type": "apiKey",
            "in": "query",
            "name": "key",
        },
        "API Authentication": {
            "type": "http",
            "scheme": "basic",
            "name": "API Authentication",
        },
        "JWT Authentication": {
            "type": "http",
            "scheme": "bearer",
            "name": "JWT Authentication",
        },
        "HeaderSecretKeyCustomException": {
            "type": "apiKey",
            "in": "header",
            "name": "key",
        },
        "DigestAuth": {"type": "http", "scheme": "digest", "name": "DigestAuth"},
    }


def test_global_guard_works():
    _app = AppFactory.create_app(global_guards=[DigestAuth])

    @get("/global")
    def _auth_demo_endpoint(request: Inject[Request]):
        return {"authentication": request.user}

    _app.router.append(_auth_demo_endpoint)
    _client = TestClient(_app)
    res = _client.get("/global")

    assert res.status_code == 401
    data = res.json()

    assert data == {"detail": "Forbidden"}
