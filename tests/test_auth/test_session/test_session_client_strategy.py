import re

import pytest
from ellar.auth.session import SessionStrategy
from ellar.auth.session.cookie_dict import SessionCookieObject
from ellar.auth.session.options import SessionCookieOption
from ellar.auth.session.strategy import SessionClientStrategy
from ellar.common import Controller, Inject, delete, get, post
from ellar.core import Config, Request
from ellar.core.router_builders import ControllerRouterBuilder
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
    test_module.override_provider(SessionStrategy, use_class=SessionClientStrategy)
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
    test_module.override_provider(SessionStrategy, use_class=SessionClientStrategy)
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
    test_module.override_provider(SessionStrategy, use_class=SessionClientStrategy)
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
                app=ControllerRouterBuilder.build(SessionSampleController),
            )
        ],
        config_module={"SECRET_KEY": "secret", "SESSION_COOKIE_PATH": "/second_app"},
    )
    test_module.override_provider(SessionStrategy, use_class=SessionClientStrategy)

    client_second_app = test_module.get_test_client(root_path="/second_app")
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
    test_module.override_provider(SessionStrategy, use_class=SessionClientStrategy)
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
    test_module.override_provider(SessionStrategy, use_class=SessionClientStrategy)
    client = test_module.get_test_client()

    response = client.post("/", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    assert "Max-Age" not in set_cookie

    client.cookies.delete("session")
    response = client.get("/")
    assert response.json() == {"session": {}}


# Unit tests for SessionClientStrategy class methods


@pytest.fixture
def config():
    """Fixture to create a config object with default session settings."""
    return Config(
        SECRET_KEY="test-secret-key",
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_DOMAIN=None,
        SESSION_COOKIE_PATH="/",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAME_SITE="lax",
        SESSION_COOKIE_MAX_AGE=14 * 24 * 60 * 60,
    )


@pytest.fixture
def strategy(config):
    """Fixture to create a SessionClientStrategy instance."""
    return SessionClientStrategy(config)


def test_session_client_strategy_initialization(config):
    """Test that SessionClientStrategy initializes correctly with config."""
    strategy = SessionClientStrategy(config)

    assert strategy.config == config
    assert strategy._signer is not None
    assert isinstance(strategy.session_cookie_options, SessionCookieOption)
    assert strategy.session_cookie_options.NAME == "session"
    assert strategy.session_cookie_options.PATH == "/"
    assert strategy.session_cookie_options.HTTPONLY is True
    assert strategy.session_cookie_options.SECURE is False
    assert strategy.session_cookie_options.SAME_SITE == "lax"
    assert strategy.session_cookie_options.MAX_AGE == 14 * 24 * 60 * 60


def test_session_client_strategy_initialization_with_custom_values():
    """Test initialization with custom config values."""
    config = Config(
        SECRET_KEY="test-secret",
        SESSION_COOKIE_NAME="custom_session",
        SESSION_COOKIE_DOMAIN="example.com",
        SESSION_COOKIE_PATH="/app",
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAME_SITE="strict",
        SESSION_COOKIE_MAX_AGE=3600,
    )
    strategy = SessionClientStrategy(config)

    assert strategy.session_cookie_options.NAME == "custom_session"
    assert strategy.session_cookie_options.DOMAIN == "example.com"
    assert strategy.session_cookie_options.PATH == "/app"
    assert strategy.session_cookie_options.HTTPONLY is False
    assert strategy.session_cookie_options.SECURE is True
    assert strategy.session_cookie_options.SAME_SITE == "strict"
    assert strategy.session_cookie_options.MAX_AGE == 3600


def test_serialize_session_with_session_cookie_object(strategy):
    """Test serializing a SessionCookieObject."""
    session = SessionCookieObject(user_id=123, username="testuser")

    result = strategy.serialize_session(session)

    assert isinstance(result, str)
    assert "session=" in result
    assert "path=/" in result
    assert "httponly" in result
    assert "samesite=lax" in result
    assert "Max-Age=1209600" in result  # 14 days in seconds


def test_serialize_session_with_empty_session_cookie_object(strategy):
    """Test serializing an empty SessionCookieObject."""
    session = SessionCookieObject()

    result = strategy.serialize_session(session)

    assert isinstance(result, str)
    assert "session=" in result


def test_serialize_session_for_deletion(strategy):
    """Test serializing a session for deletion (string input)."""
    result = strategy.serialize_session("")

    assert isinstance(result, str)
    assert "Max-Age=0" in result  # Cookie deletion flag


def test_serialize_session_with_custom_config(strategy):
    """Test serializing with custom SessionCookieOption."""
    custom_config = SessionCookieOption(
        NAME="custom_session",
        PATH="/api",
        HTTPONLY=False,
        SECURE=True,
        SAME_SITE="strict",
        MAX_AGE=3600,
    )
    session = SessionCookieObject(data="test")

    result = strategy.serialize_session(session, config=custom_config)

    assert "custom_session=" in result
    assert "path=/api" in result
    assert "samesite=strict" in result
    assert "secure" in result
    assert "Max-Age=3600" in result


def test_deserialize_session_with_valid_data(strategy):
    """Test deserializing valid session data."""
    # First serialize a session
    original_session = SessionCookieObject(user_id=456, role="admin")
    serialized = strategy.serialize_session(original_session)

    # Extract the session data from the cookie header
    session_data = serialized.split("session=")[1].split(";")[0]

    # Deserialize it
    result = strategy.deserialize_session(session_data)

    assert isinstance(result, SessionCookieObject)
    assert result["user_id"] == 456
    assert result["role"] == "admin"


def test_deserialize_session_with_none_data(strategy):
    """Test deserializing None session data returns empty SessionCookieObject."""
    result = strategy.deserialize_session(None)

    assert isinstance(result, SessionCookieObject)
    assert len(result) == 0


def test_deserialize_session_with_empty_string(strategy):
    """Test deserializing empty string returns empty SessionCookieObject."""
    result = strategy.deserialize_session("")

    assert isinstance(result, SessionCookieObject)
    assert len(result) == 0


def test_deserialize_session_with_invalid_signature(strategy):
    """Test deserializing session with invalid signature returns empty SessionCookieObject."""
    # Create invalid session data
    invalid_data = "invalid.signature.data"

    result = strategy.deserialize_session(invalid_data)

    assert isinstance(result, SessionCookieObject)
    assert len(result) == 0


def test_deserialize_session_with_tampered_data(strategy):
    """Test deserializing tampered session data returns empty SessionCookieObject."""
    # First create valid session data
    session = SessionCookieObject(user_id=789)
    serialized = strategy.serialize_session(session)
    session_data = serialized.split("session=")[1].split(";")[0]

    # Tamper with the data
    tampered_data = session_data[:-5] + "XXXXX"

    result = strategy.deserialize_session(tampered_data)

    assert isinstance(result, SessionCookieObject)
    assert len(result) == 0


def test_deserialize_session_with_custom_config(strategy):
    """Test deserializing with custom SessionCookieOption."""
    custom_config = SessionCookieOption(
        NAME="custom",
        MAX_AGE=7200,
    )

    # Serialize with custom config
    session = SessionCookieObject(test="value")
    serialized = strategy.serialize_session(session, config=custom_config)
    session_data = serialized.split("custom=")[1].split(";")[0]

    # Deserialize with same custom config
    result = strategy.deserialize_session(session_data, config=custom_config)

    assert isinstance(result, SessionCookieObject)
    assert result["test"] == "value"


def test_serialize_deserialize_round_trip(strategy):
    """Test that serialize and deserialize are inverse operations."""
    original_data = {
        "user_id": 999,
        "username": "john_doe",
        "email": "john@example.com",
        "roles": ["admin", "user"],
        "preferences": {"theme": "dark", "lang": "en"},
    }
    session = SessionCookieObject(**original_data)

    # Serialize
    serialized = strategy.serialize_session(session)
    session_data = serialized.split("session=")[1].split(";")[0]

    # Deserialize
    result = strategy.deserialize_session(session_data)

    assert dict(result) == original_data


def test_serialize_deserialize_with_unicode_characters(strategy):
    """Test serialization and deserialization with unicode characters."""
    session = SessionCookieObject(name="François", message="Hello 世界", emoji="🎉🚀")

    serialized = strategy.serialize_session(session)
    session_data = serialized.split("session=")[1].split(";")[0]

    result = strategy.deserialize_session(session_data)

    assert result["name"] == "François"
    assert result["message"] == "Hello 世界"
    assert result["emoji"] == "🎉🚀"


def test_serialize_deserialize_with_special_characters(strategy):
    """Test serialization and deserialization with special characters."""
    session = SessionCookieObject(
        special='{"key": "value"}',
        symbols="!@#$%^&*()",
    )

    serialized = strategy.serialize_session(session)
    session_data = serialized.split("session=")[1].split(";")[0]

    result = strategy.deserialize_session(session_data)

    assert result["special"] == '{"key": "value"}'
    assert result["symbols"] == "!@#$%^&*()"


def test_session_cookie_options_property(strategy):
    """Test that session_cookie_options property returns correct configuration."""
    options = strategy.session_cookie_options

    assert isinstance(options, SessionCookieOption)
    assert options.NAME == "session"
    assert options.PATH == "/"
    assert options.HTTPONLY is True
    assert options.SECURE is False


def test_signature_verification_with_different_secret_key():
    """Test that session signed with one key cannot be verified with another."""
    config1 = Config(SECRET_KEY="secret-key-1")
    config2 = Config(SECRET_KEY="secret-key-2")

    strategy1 = SessionClientStrategy(config1)
    strategy2 = SessionClientStrategy(config2)

    # Sign with strategy1
    session = SessionCookieObject(user_id=111)
    serialized = strategy1.serialize_session(session)
    session_data = serialized.split("session=")[1].split(";")[0]

    # Try to verify with strategy2 (different secret)
    result = strategy2.deserialize_session(session_data)

    assert isinstance(result, SessionCookieObject)
    assert len(result) == 0  # Should be empty due to signature mismatch


def test_session_with_nested_data_structures(strategy):
    """Test serialization and deserialization of complex nested data."""
    session = SessionCookieObject(
        user={
            "id": 123,
            "profile": {
                "name": "Test User",
                "settings": {"notifications": True, "theme": "dark"},
            },
        },
        items=[1, 2, 3, {"key": "value"}],
    )

    serialized = strategy.serialize_session(session)
    session_data = serialized.split("session=")[1].split(";")[0]

    result = strategy.deserialize_session(session_data)

    assert result["user"]["id"] == 123
    assert result["user"]["profile"]["name"] == "Test User"
    assert result["user"]["profile"]["settings"]["theme"] == "dark"
    assert result["items"] == [1, 2, 3, {"key": "value"}]
