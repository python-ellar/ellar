import pytest
from starlette.status import HTTP_401_UNAUTHORIZED

from ellar.common import Req, get, guards
from ellar.core import AppFactory, TestClient
from ellar.core.exceptions import APIException
from ellar.core.guard import (
    APIKeyCookie,
    APIKeyHeader,
    APIKeyQuery,
    HttpBasicAuth,
    HttpBearerAuth,
    HttpDigestAuth,
)
from ellar.di import injectable
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object
from ellar.services import Reflector


class CustomException(APIException):
    pass


@injectable()
class QuerySecretKeyInjectable(APIKeyQuery):
    def __init__(self, reflector: Reflector) -> None:
        super().__init__()
        self.reflector = reflector

    async def authenticate(self, connection, key):
        if key == "querysecretkey":
            return key


class QuerySecretKey(APIKeyQuery):
    async def authenticate(self, connection, key):
        if key == "querysecretkey":
            return key


class HeaderSecretKey(APIKeyHeader):
    async def authenticate(self, connection, key):
        if key == "headersecretkey":
            return key


@injectable()
class HeaderSecretKeyCustomException(HeaderSecretKey):
    exception_class = CustomException


class CookieSecretKey(APIKeyCookie):
    openapi_name = "API Key Auth"

    async def authenticate(self, connection, key):
        if key == "cookiesecretkey":
            return key


class BasicAuth(HttpBasicAuth):
    openapi_name = "API Authentication"

    async def authenticate(self, connection, credentials):
        if credentials.username == "admin" and credentials.password == "secret":
            return credentials.username


@injectable()
class BearerAuth(HttpBearerAuth):
    openapi_name = "JWT Authentication"

    async def authenticate(self, connection, credentials):
        if credentials.credentials == "bearertoken":
            return credentials.credentials


@injectable()
class DigestAuth(HttpDigestAuth):
    async def authenticate(self, connection, credentials):
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
    @guards(auth)
    def auth_demo_endpoint(request=Req()):
        return {"authentication": request.user}

    app.router.append(auth_demo_endpoint)

client = TestClient(app)

BODY_UNAUTHORIZED_DEFAULT = {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    "path,kwargs,expected_code,expected_body",
    [
        ("/apikeyquery", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeyquery?key=querysecretkey",
            {},
            200,
            dict(authentication="querysecretkey"),
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
            dict(authentication="querysecretkey"),
        ),
        ("/apikeyheader", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeyheader",
            dict(headers={"key": "headersecretkey"}),
            200,
            dict(authentication="headersecretkey"),
        ),
        ("/apikeycookie", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/apikeycookie",
            dict(cookies={"key": "cookiesecretkey"}),
            200,
            dict(authentication="cookiesecretkey"),
        ),
        ("/basic", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/basic",
            dict(headers={"Authorization": "Basic YWRtaW46c2VjcmV0"}),
            200,
            dict(authentication="admin"),
        ),
        (
            "/basic",
            dict(headers={"Authorization": "YWRtaW46c2VjcmV0"}),
            200,
            dict(authentication="admin"),
        ),
        (
            "/basic",
            dict(headers={"Authorization": "Basic invalid"}),
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        (
            "/basic",
            dict(headers={"Authorization": "some invalid value"}),
            HTTP_401_UNAUTHORIZED,
            BODY_UNAUTHORIZED_DEFAULT,
        ),
        ("/bearer", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/bearer",
            dict(headers={"Authorization": "Bearer bearertoken"}),
            200,
            dict(authentication="bearertoken"),
        ),
        (
            "/bearer",
            dict(headers={"Authorization": "Invalid bearertoken"}),
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        ("/digest", {}, 401, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/digest",
            dict(headers={"Authorization": "Digest digesttoken"}),
            200,
            dict(authentication="digesttoken"),
        ),
        (
            "/digest",
            dict(headers={"Authorization": "Invalid digesttoken"}),
            HTTP_401_UNAUTHORIZED,
            {"detail": "Invalid authentication credentials"},
        ),
        ("/customexception", {}, HTTP_401_UNAUTHORIZED, BODY_UNAUTHORIZED_DEFAULT),
        (
            "/customexception",
            dict(headers={"key": "headersecretkey"}),
            200,
            dict(authentication="headersecretkey"),
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
        "API Key Auth": {"type": "apiKey", "in": "cookie", "name": "API Key Auth"},
        "HeaderSecretKey": {
            "type": "apiKey",
            "in": "header",
            "name": "HeaderSecretKey",
        },
        "QuerySecretKey": {"type": "apiKey", "in": "query", "name": "QuerySecretKey"},
        "QuerySecretKeyInjectable": {
            "type": "apiKey",
            "in": "query",
            "name": "QuerySecretKeyInjectable",
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
            "name": "HeaderSecretKeyCustomException",
        },
        "DigestAuth": {"type": "http", "scheme": "digest", "name": "DigestAuth"},
    }
