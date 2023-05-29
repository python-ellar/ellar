import typing as t

from ellar.common import (
    Controller,
    ControllerBase,
    EllarInterceptor,
    IExecutionContext,
    UseInterceptors,
    get,
    ws_route,
)
from ellar.di import injectable
from ellar.testing import Test


@injectable
class Interceptor1(EllarInterceptor):
    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        data = await next_interceptor()
        if data:
            data.update(Interceptor1="Interceptor1 modified returned resulted")
        return data


class CustomException(Exception):
    pass


@injectable
class InterceptCustomException(EllarInterceptor):
    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        try:
            return await next_interceptor()
        except CustomException as cex:
            res = context.switch_to_http_connection().get_response()
            res.status_code = 400
            return {"message": str(cex)}


@UseInterceptors(Interceptor1)
@Controller("")
class InterceptorControllerTest(ControllerBase):
    @UseInterceptors(Interceptor1)
    @get("/interceptor-1")
    async def interceptor_1(self):
        return {"message": "intercepted okay"}

    @UseInterceptors(InterceptCustomException())
    @get("/interceptor-exception")
    async def interceptor_exception(self):
        raise CustomException("Wrong data!!")

    @ws_route("/interceptor-ws")
    async def interceptor_1_ws(self):
        ws = self.context.switch_to_websocket().get_client()
        await ws.accept()
        await ws.send_text("intercepted okay")


client = Test.create_test_module(
    controllers=[InterceptorControllerTest]
).get_test_client()


def test_interceptor_works():
    res = client.get("/interceptor-1")
    assert res.status_code == 200
    assert res.json() == {
        "Interceptor1": "Interceptor1 modified returned resulted",
        "message": "intercepted okay",
    }


def test_interceptor_works_for_exceptions():
    res = client.get("/interceptor-exception")
    assert res.status_code == 400
    assert res.json() == {"message": "Wrong data!!"}


def test_interceptor_works_ws():
    with client.websocket_connect("/interceptor-ws") as ws:
        data = ws.receive_text()
    assert data == "intercepted okay"


def test_global_guard_works():
    tm = Test.create_test_module()
    app = tm.create_application()

    @get("/global")
    def _interceptor_demo_endpoint():
        return {"message": "intercepted okay"}

    app.router.append(_interceptor_demo_endpoint)
    app.use_global_interceptors(Interceptor1(), InterceptCustomException)

    _client = tm.get_test_client()

    res = _client.get("/global")

    assert res.status_code == 200
    assert res.json() == {
        "Interceptor1": "Interceptor1 modified returned resulted",
        "message": "intercepted okay",
    }
