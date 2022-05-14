import json

import pytest

from ellar.constants import SCOPE_API_VERSIONING_RESOLVER
from ellar.core import Config, TestClient
from ellar.core.middleware import RequestVersioningMiddleware
from ellar.core.versioning import (
    DefaultAPIVersioning,
    HeaderAPIVersioning,
    HostNameAPIVersioning,
    QueryParameterAPIVersioning,
    UrlPathAPIVersioning,
)
from ellar.core.versioning.resolver import (
    DefaultAPIVersionResolver,
    HeaderVersionResolver,
    HostNameAPIVersionResolver,
    QueryParameterAPIVersionResolver,
    UrlPathVersionResolver,
)

config = Config(VERSION_RESOLVER_TYPE=DefaultAPIVersionResolver)


async def assert_version_middleware_app(scope, receive, send):
    assert scope[SCOPE_API_VERSIONING_RESOLVER]

    version_resolver = scope[SCOPE_API_VERSIONING_RESOLVER]
    assert isinstance(version_resolver, config.VERSION_RESOLVER_TYPE)

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send(
        dict(
            type="http.response.body",
            body=json.dumps({"message": "versioning scheme work"}).encode(),
        )
    )


asgi_app = RequestVersioningMiddleware(
    assert_version_middleware_app, debug=False, config=config
)


@pytest.mark.parametrize(
    "versioning_scheme, versioning_resolver_type",
    [
        (DefaultAPIVersioning(), DefaultAPIVersionResolver),
        (HeaderAPIVersioning(), HeaderVersionResolver),
        (HostNameAPIVersioning(), HostNameAPIVersionResolver),
        (QueryParameterAPIVersioning(), QueryParameterAPIVersionResolver),
        (UrlPathAPIVersioning(), UrlPathVersionResolver),
    ],
)
def test_di_middleware_execution_context_initialization(
    versioning_scheme, versioning_resolver_type
):
    config.VERSIONING_SCHEME = versioning_scheme
    config.VERSION_RESOLVER_TYPE = versioning_resolver_type

    client = TestClient(asgi_app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "versioning scheme work"
