import typing as t

import pytest
from ellar.common import IExceptionHandler, IHostContext, Inject, get, ws_route
from ellar.core import Config, WebSocket
from ellar.core.exceptions.callable_exceptions import CallableExceptionHandler
from ellar.core.exceptions.handlers import APIException, APIExceptionHandler
from ellar.core.exceptions.service import ExceptionMiddlewareService
from ellar.core.middleware import ExceptionMiddleware
from ellar.testing import Test
from pydantic.error_wrappers import ValidationError
from starlette.exceptions import HTTPException, WebSocketException
from starlette.responses import JSONResponse, Response


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


def test_exception_equality():
    exc_1 = OverrideAPIExceptionHandler()
    exc_2 = OverrideHTTPException()

    assert exc_1 != exc_2
    assert exc_1 != error_500
    assert exc_2 != exc_1
    assert exc_2 == exc_2
    assert exc_1 == exc_1


def test_invalid_handler_raise_exception():
    with pytest.raises(ValidationError) as ex:
        Config(
            EXCEPTION_HANDLERS=[InvalidExceptionHandler, OverrideAPIExceptionHandler()]
        )

    assert "Expected IExceptionHandler object," in ex.value.errors()[0]["msg"]

    with pytest.raises(ValidationError) as ex:
        Config(EXCEPTION_HANDLERS=[InvalidExceptionHandler()])

    assert "Expected IExceptionHandler object, received:" in ex.value.errors()[0]["msg"]


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
                """do nothing"""

        assert "'exception_type_or_code' must be defined" in str(ex.value)

    with pytest.raises(AssertionError) as ex:

        class InvalidExceptionSetup2(IExceptionHandler):
            exception_type_or_code = InvalidExceptionHandler

            def catch(self, ctx: IHostContext, exc: t.Any) -> t.Union[Response, t.Any]:
                """do nothing"""

        assert "'exception_type_or_code' is not a valid type" in str(ex.value)


def test_custom_exception_works():
    @get()
    def homepage():
        raise NewException("New Exception")

    tm = Test.create_test_module(
        routers=[homepage],
        config_module={"EXCEPTION_HANDLERS": [NewExceptionHandler()]},
    )

    client = tm.get_test_client()
    res = client.get("/")
    assert res.status_code == 400
    assert res.json() == {"detail": "New Exception"}


def test_exception_override_works():
    @get()
    def homepage():
        raise APIException("New APIException")

    tm = Test.create_test_module(
        routers=[homepage],
        config_module={"EXCEPTION_HANDLERS": [OverrideAPIExceptionHandler()]},
    )

    client = tm.get_test_client()
    res = client.get("/")
    assert res.status_code == 404
    assert res.json() == {"detail": "New APIException"}


@pytest.mark.parametrize(
    "exception_handler",
    [
        CallableExceptionHandler(exc_or_status_code=500, handler=error_500),
        ServerErrorHandler(),
    ],
)
def test_500_error_as_a_function(exception_handler):
    @get()
    def homepage():
        raise RuntimeError("Server Error")

    tm = Test.create_test_module(
        routers=[homepage], config_module={"EXCEPTION_HANDLERS": [exception_handler]}
    )

    client = tm.get_test_client(raise_server_exceptions=False)
    res = client.get("/")
    assert res.status_code == 500
    assert res.json() == {"detail": "Server Error"}


def test_raise_default_http_exception():
    @get()
    def homepage():
        raise HTTPException(detail="Bad Request", status_code=400)

    tm = Test.create_test_module(routers=[homepage])

    client = tm.get_test_client()
    res = client.get("/")
    assert res.status_code == 400
    assert res.json() == {"detail": "Bad Request", "status_code": 400}


@pytest.mark.parametrize("status_code", [204, 304])
def test_raise_default_http_exception_for_204_and_304(status_code):
    @get()
    def homepage():
        raise HTTPException(detail="Server Error", status_code=status_code)

    tm = Test.create_test_module(routers=[homepage])

    client = tm.get_test_client()
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
        config=Config(DEBUG=True),
        exception_middleware_service=ExceptionMiddlewareService(),
    )
    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        client.get("/")


def test_application_add_exception_handler():
    @get()
    def homepage():
        raise HTTPException(detail="Bad Request", status_code=400)

    tm = Test.create_test_module(
        routers=[homepage],
        config_module={"EXCEPTION_HANDLERS": [OverrideHTTPException()]},
    )

    client = tm.get_test_client()
    res = client.get("/")

    assert res.status_code == 400
    assert res.json() == {"detail": "HttpException Override"}


def test_application_http_exception_handler_raise_exception_for_returning_none():
    @get()
    def homepage():
        raise HTTPException(detail="Bad Request", status_code=400)

    tm = Test.create_test_module(
        routers=[homepage],
        config_module={"EXCEPTION_HANDLERS": [RuntimeHTTPException()]},
    )

    with pytest.raises(
        RuntimeError, match="HTTP ExceptionHandler must return a response."
    ):
        tm.get_test_client().get("/")


def test_application_adding_same_exception_twice():
    tm = Test.create_test_module()
    app = tm.create_application()

    exception = OverrideHTTPException()
    app.add_exception_handler(exception)
    assert exception is app.config.EXCEPTION_HANDLERS[1]

    exception2 = OverrideHTTPException()
    app.add_exception_handler(exception2)
    assert exception2 is not app.config.EXCEPTION_HANDLERS[1]
    assert exception is app.config.EXCEPTION_HANDLERS[1]


def test_callable_exception_handler_equality():
    def exception_handler_fun(ctx, exc: Exception):
        return "Bad Request"

    exception_400_handler = CallableExceptionHandler(
        exc_or_status_code=400, handler=exception_handler_fun
    )
    exception_500_handler = CallableExceptionHandler(
        exc_or_status_code=500, handler=exception_handler_fun
    )

    assert exception_500_handler != exception_400_handler
    assert exception_500_handler != exception_handler_fun
    assert exception_400_handler == exception_400_handler
    assert exception_500_handler == exception_500_handler


@pytest.mark.parametrize("exc", [APIException, HTTPException])
def test_http_exception_handler_case_1(exc):
    @get("/case_1")
    def homepage():
        raise exc(detail=["Bad Request"], status_code=400)

    @get("/case_2")
    def homepage_2():
        raise exc(detail={"message": "Bad Request"}, status_code=400)

    tm = Test.create_test_module(routers=[homepage, homepage_2])
    client = tm.get_test_client()

    res = client.get("/case_1")
    assert res.status_code == 400
    assert res.json() == ["Bad Request"]

    res = client.get("/case_2")
    assert res.status_code == 400
    assert res.json() == {"message": "Bad Request"}


def test_ws_exception_handler():
    homepage_3_called = False

    @ws_route("/ws")
    async def homepage_3(session: Inject[WebSocket]):
        nonlocal homepage_3_called

        homepage_3_called = True
        await session.accept()
        raise WebSocketException(reason="bad request", code=1001)

    tm = Test.create_test_module(routers=[homepage_3])
    client = tm.get_test_client()

    with client.websocket_connect("/ws"):
        pass

    assert homepage_3_called
