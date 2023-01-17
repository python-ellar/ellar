import typing as t
from unittest.mock import patch

import pytest
from pydantic.error_wrappers import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from ellar.common import get
from ellar.core import Config, TestClientFactory
from ellar.core.context import IHostContext
from ellar.core.exceptions.callable_exceptions import CallableExceptionHandler
from ellar.core.exceptions.handlers import APIException, APIExceptionHandler
from ellar.core.exceptions.interfaces import IExceptionHandler
from ellar.core.exceptions.service import ExceptionMiddlewareService
from ellar.core.middleware import ExceptionMiddleware


class InvalidExceptionHandler:
    pass


class NewException(Exception):
    pass


class NewExceptionHandler(IExceptionHandler):
    exception_type_or_code = NewException

    async def catch(
        self, ctx: IHostContext, exc: t.Union[t.Any, Exception]
    ) -> t.Union[Response, t.Any]:
        return JSONResponse({"detail": str(exc)}, status_code=400)


class OverrideAPIExceptionHandler(APIExceptionHandler):
    async def catch(
        self, ctx: IHostContext, exc: t.Union[t.Any, Exception]
    ) -> t.Union[Response, t.Any]:
        return JSONResponse({"detail": str(exc)}, status_code=404)


class OverrideHTTPException(IExceptionHandler):
    exception_type_or_code = HTTPException

    async def catch(
        self, ctx: IHostContext, exc: t.Union[t.Any, Exception]
    ) -> t.Union[Response, t.Any]:
        return JSONResponse({"detail": "HttpException Override"}, status_code=400)


class RuntimeHTTPException(IExceptionHandler):
    exception_type_or_code = HTTPException

    async def catch(
        self, ctx: IHostContext, exc: t.Union[t.Any, Exception]
    ) -> t.Union[Response, t.Any]:
        return None


class ServerErrorHandler(IExceptionHandler):
    exception_type_or_code = 500

    async def catch(
        self, ctx: IHostContext, exc: t.Union[t.Any, Exception]
    ) -> t.Union[Response, t.Any]:
        return JSONResponse({"detail": "Server Error"}, status_code=500)


def error_500(ctx: IHostContext, exc: Exception):
    assert isinstance(ctx, IHostContext)
    return JSONResponse({"detail": "Server Error"}, status_code=500)


def test_invalid_handler_raise_exception():
    with pytest.raises(ValidationError) as ex:
        Config(EXCEPTION_HANDLERS=[InvalidExceptionHandler])

    assert ex.value.errors() == [
        {
            "loc": ("EXCEPTION_HANDLERS", 0),
            "msg": "Expected TExceptionHandler, received: <class 'tests.test_exceptions.test_custom_exceptions.InvalidExceptionHandler'>",
            "type": "value_error",
        }
    ]

    with pytest.raises(ValidationError) as ex:
        Config(EXCEPTION_HANDLERS=[InvalidExceptionHandler()])

    assert ex.value.errors() == [
        {
            "loc": ("EXCEPTION_HANDLERS", 0),
            "msg": "Expected TExceptionHandler, received: "
            "<class 'tests.test_exceptions.test_custom_exceptions.InvalidExceptionHandler'>",
            "type": "value_error",
        }
    ]


def test_invalid_exception_handler_setup_raise_exception():
    with pytest.raises(AssertionError) as ex:

        class InvalidExceptionSetup(IExceptionHandler):
            def catch(self, ctx: IHostContext, exc: t.Any) -> t.Union[Response, t.Any]:
                pass

    assert "'exception_type_or_code' must be defined" in str(ex.value)


def test_invalid_exception_type_setup_raise_exception():
    with pytest.raises(AssertionError) as ex:

        class InvalidExceptionSetup(IExceptionHandler):
            exception_type_or_code = ""

            def catch(self, ctx: IHostContext, exc: t.Any) -> t.Union[Response, t.Any]:
                pass

        assert "'exception_type_or_code' must be defined" in str(ex.value)

    with pytest.raises(AssertionError) as ex:

        class InvalidExceptionSetup2(IExceptionHandler):
            exception_type_or_code = InvalidExceptionHandler

            def catch(self, ctx: IHostContext, exc: t.Any) -> t.Union[Response, t.Any]:
                pass

        assert "'exception_type_or_code' is not a valid type" in str(ex.value)


def test_custom_exception_works():
    @get()
    def homepage():
        raise NewException("New Exception")

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    tm.app.add_exception_handler(NewExceptionHandler())

    client = tm.get_client()
    res = client.get("/")
    assert res.status_code == 400
    assert res.json() == {"detail": "New Exception"}


def test_exception_override_works():
    @get()
    def homepage():
        raise APIException("New APIException")

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    tm.app.add_exception_handler(OverrideAPIExceptionHandler())

    client = tm.get_client()
    res = client.get("/")
    assert res.status_code == 404
    assert res.json() == {"detail": "New APIException"}


@pytest.mark.parametrize(
    "exception_handler",
    [
        CallableExceptionHandler(
            exc_class_or_status_code=500, callable_exception_handler=error_500
        ),
        ServerErrorHandler(),
    ],
)
def test_500_error_as_a_function(exception_handler):
    @get()
    def homepage():
        raise RuntimeError("Server Error")

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    tm.app.add_exception_handler(exception_handler)

    client = tm.get_client(raise_server_exceptions=False)
    res = client.get("/")
    assert res.status_code == 500
    assert res.json() == {"detail": "Server Error"}


def test_raise_default_http_exception():
    @get()
    def homepage():
        raise HTTPException(detail="Bad Request", status_code=400)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    client = tm.get_client()
    res = client.get("/")
    assert res.status_code == 400
    assert res.json() == {"detail": "Bad Request", "status_code": 400}


@pytest.mark.parametrize("status_code", [204, 304])
def test_raise_default_http_exception_for_204_and_304(status_code):
    @get()
    def homepage():
        raise HTTPException(detail="Server Error", status_code=status_code)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)

    client = tm.get_client()
    res = client.get("/")
    assert res.status_code == status_code
    assert res.text == ""


def test_debug_after_response_sent(test_client_factory):
    async def app(scope, receive, send):
        response = Response(b"", status_code=204)
        await response(scope, receive, send)
        raise RuntimeError("Something went wrong")

    app = ExceptionMiddleware(
        app,
        debug=True,
        exception_middleware_service=ExceptionMiddlewareService(),
    )
    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        client.get("/")


def test_application_add_exception_handler():
    @get()
    def homepage():
        raise HTTPException(detail="Bad Request", status_code=400)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    tm.app.add_exception_handler(OverrideHTTPException())

    client = tm.get_client()
    res = client.get("/")

    assert res.status_code == 400
    assert res.json() == {"detail": "HttpException Override"}


def test_application_http_exception_handler_raise_exception_for_returning_none():
    @get()
    def homepage():
        raise HTTPException(detail="Bad Request", status_code=400)

    tm = TestClientFactory.create_test_module()
    tm.app.router.append(homepage)
    tm.app.add_exception_handler(RuntimeHTTPException())
    with pytest.raises(
        RuntimeError, match="HTTP ExceptionHandler must return a response."
    ):
        tm.get_client().get("/")


def test_application_adding_same_exception_twice():
    tm = TestClientFactory.create_test_module()
    with patch.object(
        tm.app.__class__, "rebuild_middleware_stack"
    ) as rebuild_middleware_stack_mock:
        tm.app.add_exception_handler(OverrideHTTPException())
    rebuild_middleware_stack_mock.assert_called()

    with patch.object(
        tm.app.__class__, "rebuild_middleware_stack"
    ) as rebuild_middleware_stack_mock:
        tm.app.add_exception_handler(OverrideHTTPException())
    assert rebuild_middleware_stack_mock.call_count == 0
