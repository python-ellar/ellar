from ellar.common import middleware
from ellar.common.compatible import AttributeDict
from ellar.common.constants import MIDDLEWARE_HANDLERS_KEY


@middleware()
def middleware_function_test():
    pass  # pragma: no cover


def test_middleware_decorator_works():
    assert hasattr(middleware_function_test, MIDDLEWARE_HANDLERS_KEY)
    middleware_detail: AttributeDict = getattr(
        middleware_function_test, MIDDLEWARE_HANDLERS_KEY
    )
    assert middleware_detail.dispatch is middleware_function_test
    assert middleware_detail.options == {}
