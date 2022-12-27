import http

import pytest

from ellar.common import get
from ellar.core import TestClientFactory
from ellar.core.exceptions import (
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
        (
            APIException,
            APIException.status_code,
            http.HTTPStatus(APIException.status_code).phrase,
        ),
        (
            AuthenticationFailed,
            AuthenticationFailed.status_code,
            "Incorrect authentication credentials.",
        ),
        (
            NotAcceptable,
            NotAcceptable.status_code,
            http.HTTPStatus(NotAcceptable.status_code).phrase,
        ),
        (
            NotAuthenticated,
            NotAuthenticated.status_code,
            http.HTTPStatus(NotAuthenticated.status_code).phrase,
        ),
        (NotFound, NotFound.status_code, http.HTTPStatus(NotFound.status_code).phrase),
        (
            PermissionDenied,
            PermissionDenied.status_code,
            http.HTTPStatus(PermissionDenied.status_code).phrase,
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
    _exception_runner = ExceptionRunner(UnsupportedMediaType)
    response = client.get("/exception")
    data = response.json()
    assert response.status_code == UnsupportedMediaType.status_code
    assert data["detail"] == http.HTTPStatus(UnsupportedMediaType.status_code).phrase


def test_method_not_allowed_api_exception():
    global _exception_runner
    _exception_runner = ExceptionRunner(MethodNotAllowed)
    response = client.get("/exception")
    data = response.json()
    assert response.status_code == MethodNotAllowed.status_code
    assert data["detail"] == http.HTTPStatus(MethodNotAllowed.status_code).phrase
