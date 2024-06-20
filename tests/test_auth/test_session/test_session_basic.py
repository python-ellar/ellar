import pytest
from ellar.auth.session import SessionServiceNullStrategy, SessionStrategy
from ellar.auth.session.strategy import SessionClientStrategy
from ellar.common import Inject, get
from ellar.core import Request
from ellar.testing import Test


@get()
def homepage(req: Inject[Request]):
    return req.session


tm = Test.create_test_module()
tm.create_application().router.add_route(homepage)


def test_session_object_raise_an_exception():
    session_service = tm.get(SessionStrategy)
    assert isinstance(session_service, SessionServiceNullStrategy)

    with pytest.raises(AssertionError):
        client = tm.get_test_client()
        client.get("/")


def test_session_object_raise_an_exception_case_2():
    tm_case_2 = Test.create_test_module(config_module={"SESSION_DISABLED": True})
    tm_case_2.override_provider(SessionStrategy, use_class=SessionClientStrategy)
    tm_case_2.create_application().router.add_route(homepage)
    session_service = tm_case_2.get(SessionStrategy)
    assert isinstance(session_service, SessionClientStrategy)

    with pytest.raises(AssertionError):
        client = tm_case_2.get_test_client()
        client.get("/")
