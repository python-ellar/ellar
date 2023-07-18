from ellar.auth.session import SessionCookieObject


def test_accessed_property_is_true_when_dict_values_are_accessed():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.accessed is False

    name = session_cookie.get("name")
    assert name == "Ellar"

    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.accessed is False
    assert session_cookie.name == "Ellar"
    assert session_cookie.accessed is True


def test_modified_property_is_true_when_dict_values_are_updated():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    assert session_cookie.accessed is False

    session_cookie.name = "Cookie Session"
    assert session_cookie.modified is True
    assert session_cookie.accessed is True

    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    assert session_cookie.accessed is False

    session_cookie.some_new_value = "some_new_value"
    assert session_cookie.modified is True
    assert session_cookie.accessed is True
    assert session_cookie.get("some_new_value") == "some_new_value"


def test_del_modifier_function():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    del session_cookie["name"]
    assert session_cookie.modified is True
    assert "name" not in session_cookie


def test_pop_modifier_function():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    session_cookie.pop("name")
    assert session_cookie.modified is True
    assert "name" not in session_cookie


def test_popitem_modifier_function():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    session_cookie.popitem()
    assert session_cookie.modified is True


def test_clear_modifier_function():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    session_cookie.clear()
    assert session_cookie.modified is True


def test_setdefault_modifier_function():
    session_cookie = SessionCookieObject(name="Ellar", author="ellar@example.com", id=2)
    assert session_cookie.modified is False
    session_cookie.setdefault("asgi", "python")
    assert session_cookie.modified is True
    assert session_cookie.asgi == "python"
