from ellar.auth.handlers import (
    CookieAPIKeyAuthenticationHandler,
    HeaderAPIKeyAuthenticationHandler,
    HttpBasicAuthenticationHandler,
    HttpBearerAuthenticationHandler,
    QueryAPIKeyAuthenticationHandler,
)
from ellar.common import serialize_object
from ellar.core import Reflector
from ellar.di import injectable
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test


@injectable()
class QueryAuth(QueryAPIKeyAuthenticationHandler):
    def __init__(self, reflector: Reflector) -> None:
        super().__init__()
        self.reflector = reflector

    async def authentication_handler(self, context, key):
        if key == "querysecretkey":
            return key


class HeaderAuth(HeaderAPIKeyAuthenticationHandler):
    async def authentication_handler(self, context, key):
        if key == "headersecretkey":
            return key


class CookieAuth(CookieAPIKeyAuthenticationHandler):
    openapi_name = "API Key Auth"

    async def authentication_handler(self, context, key):
        if key == "cookiesecretkey":
            return key


class BasicAuth(HttpBasicAuthenticationHandler):
    openapi_name = "API Authentication"

    async def authentication_handler(self, context, credentials):
        if credentials.username == "admin" and credentials.password == "secret":
            return credentials.username


@injectable()
class BearerAuth(HttpBearerAuthenticationHandler):
    openapi_name = "JWT Authentication"

    async def authentication_handler(self, context, credentials):
        if credentials.credentials == "bearertoken":
            return credentials.credentials


test_module = Test.create_test_module()
app = test_module.create_application()
app.add_authentication_schemes(BearerAuth, HeaderAuth, QueryAuth, CookieAuth, BasicAuth)


def test_openapi_auth_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document["components"]["securitySchemes"] == {
        "JWT Authentication": {
            "type": "http",
            "scheme": "bearer",
            "name": "JWT Authentication",
        },
        "HeaderAuth": {"type": "apiKey", "in": "header", "name": "key"},
        "QueryAuth": {"type": "apiKey", "in": "query", "name": "key"},
        "API Key Auth": {"type": "apiKey", "in": "cookie", "name": "key"},
        "API Authentication": {
            "type": "http",
            "scheme": "basic",
            "name": "API Authentication",
        },
    }

    assert document.get("security", []) == []
