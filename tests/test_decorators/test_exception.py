from ellar.common import exception_handler
from ellar.common.constants import EXCEPTION_HANDLERS_KEY


class CustomException(Exception):
    pass


@exception_handler(CustomException)
def exception_decorator_test():
    """ignore"""


@exception_handler(exc_or_status_code=404, app=True)
def exception_decorator_test_2():
    """ignore"""


def test_exception_decorators_sets_exception_key():
    assert hasattr(exception_decorator_test, EXCEPTION_HANDLERS_KEY)
    exception_details: dict = getattr(exception_decorator_test, EXCEPTION_HANDLERS_KEY)
    assert exception_details[CustomException] == (exception_decorator_test, False)

    exception_details: dict = getattr(
        exception_decorator_test_2, EXCEPTION_HANDLERS_KEY
    )
    assert exception_details[404] == (exception_decorator_test_2, True)
