import pytest

from ellar.common import get
from ellar.core import TestClientFactory
from ellar.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    UnsupportedMediaType,
)

from .exception_runner import ExceptionRunner

test_module = TestClientFactory.create_test_module()


_exception_runner = ExceptionRunner(APIException)


@get("/exception")
def exception_():
    _exception_runner.run()


test_module.app.router.append(exception_)
client = test_module.get_client()


@pytest.mark.parametrize(
    "exception, status_code, default_detail",
    [
        (APIException, APIException.status_code, APIException.default_detail),
        (
            AuthenticationFailed,
            AuthenticationFailed.status_code,
            AuthenticationFailed.default_detail,
        ),
        (NotAcceptable, NotAcceptable.status_code, NotAcceptable.default_detail),
        (
            NotAuthenticated,
            NotAuthenticated.status_code,
            NotAuthenticated.default_detail,
        ),
        (NotFound, NotFound.status_code, NotFound.default_detail),
        (
            PermissionDenied,
            PermissionDenied.status_code,
            PermissionDenied.default_detail,
        ),
    ],
)
def test_api_exception(exception, status_code, default_detail):
    global _exception_runner
    _exception_runner = ExceptionRunner(exception)
    response = client.get("/exception")
    data = response.json()
    assert response.status_code == status_code
    assert data["detail"] == default_detail


def test_unsupported_media_type_api_exception():
    global _exception_runner
    media_type = "application/json/sx"
    _exception_runner = ExceptionRunner(UnsupportedMediaType, media_type=media_type)
    response = client.get("/exception")
    data = response.json()
    assert response.status_code == UnsupportedMediaType.status_code
    assert data["detail"] == UnsupportedMediaType.default_detail.format(
        media_type=media_type
    )


def test_method_not_allowed_api_exception():
    global _exception_runner
    method = "GET"
    _exception_runner = ExceptionRunner(MethodNotAllowed, method=method)
    response = client.get("/exception")
    data = response.json()
    assert response.status_code == MethodNotAllowed.status_code
    assert data["detail"] == MethodNotAllowed.default_detail.format(method=method)
