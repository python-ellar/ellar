from ellar.common import middleware
from ellar.constants import MIDDLEWARE_HANDLERS_KEY
from ellar.core.middleware import FunctionBasedMiddleware
from ellar.core.middleware.schema import MiddlewareSchema


@middleware()
def middleware_function_test():
    pass  # pragma: no cover


def test_middleware_decorator_works():
    assert hasattr(middleware_function_test, MIDDLEWARE_HANDLERS_KEY)
    middleware_detail: MiddlewareSchema = getattr(
        middleware_function_test, MIDDLEWARE_HANDLERS_KEY
    )
    assert middleware_detail.middleware_class is FunctionBasedMiddleware
    assert middleware_detail.dispatch is middleware_function_test
