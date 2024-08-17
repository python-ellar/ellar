from ellar.common import middleware
from ellar.common.compatible import AttributeDict
from ellar.common.constants import MIDDLEWARE_HANDLERS_KEY


@middleware()
def middleware_function_test():
    pass  # pragma: no cover


@middleware(app=True)
def middleware_function_app_scope():
    pass  # pragma: no cover


def test_middleware_decorator_works():
    assert hasattr(middleware_function_test, MIDDLEWARE_HANDLERS_KEY)
    middleware_detail: AttributeDict = getattr(
        middleware_function_test, MIDDLEWARE_HANDLERS_KEY
    )
    assert middleware_detail.dispatch is middleware_function_test
    assert middleware_detail.options == {}
    assert middleware_detail.is_global is False


def test_middleware_decorator_works_at_app_scope():
    assert hasattr(middleware_function_app_scope, MIDDLEWARE_HANDLERS_KEY)
    middleware_detail: AttributeDict = getattr(
        middleware_function_app_scope, MIDDLEWARE_HANDLERS_KEY
    )
    assert middleware_detail.dispatch is middleware_function_app_scope
    assert middleware_detail.options == {}
    assert middleware_detail.is_global is True
