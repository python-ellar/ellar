from ellar.common import Inject, http_route
from ellar.testing import Test
from starlette.requests import Request
from starlette.responses import PlainTextResponse


def test_cors_allow_all():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_EXPOSE_HEADERS": ["X-Status"],
            "CORS_ALLOW_HEADERS": ["*"],
            "CORS_ALLOW_METHODS": ["*"],
            "CORS_ALLOW_ORIGINS": ["*"],
            "CORS_ALLOW_CREDENTIALS": True,
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))
    client = tm.get_test_client()

    # Test pre-flight response
    headers = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "OK"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert response.headers["access-control-allow-headers"] == "X-Example"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["vary"] == "Origin"

    # Test standard response
    headers = {"Origin": "https://example.org"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-expose-headers"] == "X-Status"
    assert response.headers["access-control-allow-credentials"] == "true"

    # Test standard credentialed response
    headers = {"Origin": "https://example.org", "Cookie": "star_cookie=sugar"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert response.headers["access-control-expose-headers"] == "X-Status"
    assert response.headers["access-control-allow-credentials"] == "true"

    # Test non-CORS response
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert "access-control-allow-origin" not in response.headers


def test_cors_allow_all_except_credentials():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_EXPOSE_HEADERS": ["X-Status"],
            "CORS_ALLOW_HEADERS": ["*"],
            "CORS_ALLOW_METHODS": ["*"],
            "CORS_ALLOW_ORIGINS": ["*"],
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    # Test pre-flight response
    headers = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "OK"
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-headers"] == "X-Example"
    assert "access-control-allow-credentials" not in response.headers
    assert "vary" not in response.headers

    # Test standard response
    headers = {"Origin": "https://example.org"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-expose-headers"] == "X-Status"
    assert "access-control-allow-credentials" not in response.headers

    # Test non-CORS response
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert "access-control-allow-origin" not in response.headers


def test_cors_allow_specific_origin():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_ALLOW_HEADERS": ["X-Example", "Content-Type"],
            "CORS_ALLOW_ORIGINS": ["https://example.org"],
            "CORS_ALLOW_CREDENTIALS": False,
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    # Test pre-flight response
    headers = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example, Content-Type",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "OK"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert response.headers["access-control-allow-headers"] == (
        "Accept, Accept-Language, Content-Language, Content-Type, X-Example"
    )
    assert "access-control-allow-credentials" not in response.headers

    # Test standard response
    headers = {"Origin": "https://example.org"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert "access-control-allow-credentials" not in response.headers

    # Test non-CORS response
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert "access-control-allow-origin" not in response.headers


def test_cors_disallowed_preflight():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_ALLOW_HEADERS": ["X-Example"],
            "CORS_ALLOW_ORIGINS": ["https://example.org"],
        }
    )
    app = tm.create_application()

    app.router.append(http_route(methods=["GET"])(homepage))
    client = tm.get_test_client()

    # Test pre-flight response
    headers = {
        "Origin": "https://another.org",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "X-Nope",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin, method, headers"
    assert "access-control-allow-origin" not in response.headers

    # Bug specific test, https://github.com/encode/starlette/pull/1199
    # Test preflight response text with multiple disallowed headers
    headers = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Nope-1, X-Nope-2",
    }
    response = client.options("/", headers=headers)
    assert response.text == "Disallowed CORS headers"


def test_preflight_allows_request_origin_if_origins_wildcard_and_credentials_allowed():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_ALLOW_ORIGINS": ["*"],
            "CORS_ALLOW_METHODS": ["POST"],
            "CORS_ALLOW_CREDENTIALS": True,
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    # Test pre-flight response
    headers = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "POST",
    }

    response = client.options(
        "/",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["vary"] == "Origin"


def test_cors_preflight_allow_all_methods():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={"CORS_ALLOW_ORIGINS": ["*"], "CORS_ALLOW_METHODS": ["*"]}
    )
    app = tm.create_application()

    app.router.append(http_route(methods=["GET"])(homepage))
    client = tm.get_test_client()

    headers = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "POST",
    }

    for method in ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"):
        response = client.options("/", headers=headers)
        assert response.status_code == 200
        assert method in response.headers["access-control-allow-methods"]


def test_cors_allow_all_methods():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    methods = ["delete", "get", "head", "options", "patch", "post", "put"]
    tm = Test.create_test_module(
        config_module={"CORS_ALLOW_ORIGINS": ["*"], "CORS_ALLOW_METHODS": ["*"]}
    )
    app = tm.create_application()
    app.router.append(http_route(methods=methods)(homepage))
    client = tm.get_test_client()

    headers = {"Origin": "https://example.org"}

    for method in ("patch", "post", "put"):
        response = getattr(client, method)("/", headers=headers, json={})
        assert response.status_code == 200
    for method in ("delete", "get", "head", "options"):
        response = getattr(client, method)("/", headers=headers)
        assert response.status_code == 200


def test_cors_allow_origin_regex():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_ALLOW_ORIGIN_REGEX": "https://.*",
            "CORS_ALLOW_HEADERS": ["X-Example", "Content-Type"],
            "CORS_ALLOW_CREDENTIALS": True,
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    # Test standard response
    headers = {"Origin": "https://example.org"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert response.headers["access-control-allow-credentials"] == "true"

    # Test standard credentialed response
    headers = {"Origin": "https://example.org", "Cookie": "star_cookie=sugar"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert response.headers["access-control-allow-credentials"] == "true"

    # Test disallowed standard response
    # Note that enforcement is a browser concern. The disallowed-ness is reflected
    # in the lack of an "access-control-allow-origin" header in the response.
    headers = {"Origin": "http://example.org"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert "access-control-allow-origin" not in response.headers

    # Test pre-flight response
    headers = {
        "Origin": "https://another.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example, content-type",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "OK"
    assert response.headers["access-control-allow-origin"] == "https://another.com"
    assert response.headers["access-control-allow-headers"] == (
        "Accept, Accept-Language, Content-Language, Content-Type, X-Example"
    )
    assert response.headers["access-control-allow-credentials"] == "true"

    # Test disallowed pre-flight response
    headers = {
        "Origin": "http://another.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 400
    assert response.text == "Disallowed CORS origin"
    assert "access-control-allow-origin" not in response.headers


def test_cors_allow_origin_regex_fullmatch():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_ALLOW_ORIGIN_REGEX": r"https://.*\.example.org",
            "CORS_ALLOW_HEADERS": ["X-Example", "Content-Type"],
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    # Test standard response
    headers = {"Origin": "https://subdomain.example.org"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert (
        response.headers["access-control-allow-origin"]
        == "https://subdomain.example.org"
    )
    assert "access-control-allow-credentials" not in response.headers

    # Test diallowed standard response
    headers = {"Origin": "https://subdomain.example.org.hacker.com"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert "access-control-allow-origin" not in response.headers


def test_cors_credentialed_requests_return_specific_origin():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(config_module={"CORS_ALLOW_ORIGINS": ["*"]})
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))
    client = tm.get_test_client()

    # Test credentialed request
    headers = {"Origin": "https://example.org", "Cookie": "star_cookie=sugar"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.text == "Homepage"
    assert response.headers["access-control-allow-origin"] == "https://example.org"
    assert "access-control-allow-credentials" not in response.headers


def test_cors_vary_header_defaults_to_origin():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={"CORS_ALLOW_ORIGINS": ["https://example.org"]}
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    headers = {"Origin": "https://example.org"}

    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["vary"] == "Origin"


def test_cors_vary_header_is_not_set_for_non_credentialed_request():
    def homepage(request: Inject[Request]):
        return PlainTextResponse(
            "Homepage", status_code=200, headers={"Vary": "Accept-Encoding"}
        )

    tm = Test.create_test_module(config_module={"CORS_ALLOW_ORIGINS": ["*"]})
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    response = client.get("/", headers={"Origin": "https://someplace.org"})
    assert response.status_code == 200
    assert response.headers["vary"] == "Accept-Encoding"


def test_cors_vary_header_is_properly_set_for_credentialed_request():
    def homepage(request: Inject[Request]):
        return PlainTextResponse(
            "Homepage", status_code=200, headers={"Vary": "Accept-Encoding"}
        )

    tm = Test.create_test_module(config_module={"CORS_ALLOW_ORIGINS": ["*"]})
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))
    client = tm.get_test_client()

    response = client.get(
        "/", headers={"Cookie": "foo=bar", "Origin": "https://someplace.org"}
    )
    assert response.status_code == 200
    assert response.headers["vary"] == "Accept-Encoding, Origin"


def test_cors_vary_header_is_properly_set_when_allow_origins_is_not_wildcard():
    def homepage(request: Inject[Request]):
        return PlainTextResponse(
            "Homepage", status_code=200, headers={"Vary": "Accept-Encoding"}
        )

    tm = Test.create_test_module(
        config_module={"CORS_ALLOW_ORIGINS": ["https://example.org"]}
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))

    client = tm.get_test_client()

    response = client.get("/", headers={"Origin": "https://example.org"})
    assert response.status_code == 200
    assert response.headers["vary"] == "Accept-Encoding, Origin"


def test_cors_allowed_origin_does_not_leak_between_credentialed_requests():
    def homepage(request: Inject[Request]):
        return PlainTextResponse("Homepage", status_code=200)

    tm = Test.create_test_module(
        config_module={
            "CORS_ALLOW_ORIGINS": ["*"],
            "CORS_ALLOW_HEADERS": ["*"],
            "CORS_ALLOW_METHODS": ["*"],
        }
    )
    app = tm.create_application()
    app.router.append(http_route(methods=["GET"])(homepage))
    client = tm.get_test_client()

    response = client.get("/", headers={"Origin": "https://someplace.org"})
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers

    response = client.get(
        "/", headers={"Cookie": "foo=bar", "Origin": "https://someplace.org"}
    )
    assert response.headers["access-control-allow-origin"] == "https://someplace.org"
    assert "access-control-allow-credentials" not in response.headers

    response = client.get("/", headers={"Origin": "https://someplace.org"})
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers
