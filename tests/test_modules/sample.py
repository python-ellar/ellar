from typing import Optional

from ellar.common import (
    Body,
    Controller,
    Module,
    ModuleRouter,
    Ws,
    exception_handler,
    middleware,
    on_shutdown,
    on_startup,
    put,
    template_filter,
    template_global,
    ws_route,
)
from ellar.core import App, Config
from ellar.core.connection import WebSocket
from ellar.core.modules import ModuleBase
from ellar.di import ProviderConfig

from ..schema import Item, User


class UserService:
    def __init__(self):
        self.user = User(username="username", full_name="full_name")


class AnotherUserService(UserService):
    pass


@Controller(
    "/items/{orgID:int}",
    tag="Item",
    description="Sample Controller",
    external_doc_url="https://test.com",
    external_doc_description="Find out more here",
)
class SampleController:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    @put("/{item_id:uuid}")
    async def update_item(
        self,
        *,
        item_id: int,
        item: Item,
        user: User,
        importance: int = Body(gt=0),
        q: Optional[str] = None
    ):
        results = {
            "item_id": item_id,
            "item": item,
            "user": user,
            "importance": importance,
        }
        if q:
            results.update({"q": q})
        results.update(self._user_service.user)
        return results

    @ws_route("/websocket")
    async def websocket_test(self, *, web_socket: WebSocket = Ws()):
        await web_socket.accept()
        await web_socket.send_json({"message": "Websocket okay"})
        await web_socket.close()


mr = ModuleRouter("/mr")


@mr.get("/get")
def get_mr():
    return {"get_mr", "OK"}


@mr.post("/post")
def post_mr():
    return {"post_mr", "OK"}


class ModuleBaseExample(ModuleBase):
    _before_init_called = False
    _app_ready_called = False

    @exception_handler(404)
    async def exception_404(cls, request, exc):
        pass

    @middleware("http")
    async def middleware(cls, request, call_next):
        response = await call_next(request)
        return response

    @template_global()
    def some_template_global(cls, n):
        pass

    @template_filter()
    def some_template_filter(cls, n):
        pass

    @classmethod
    def before_init(cls, config: Config) -> None:
        cls._before_init_called = True

    def application_ready(self, app: "App") -> None:
        self.__class__._app_ready_called = True

    @on_startup
    async def on_startup_handler(cls):
        pass

    @on_shutdown
    def on_shutdown_handler(cls):
        pass


ModuleBaseExample2 = type("ModuleBaseExample2", (ModuleBaseExample,), {})

SampleModule = Module(
    controllers=(SampleController,),
    routers=(mr,),
    providers=(
        UserService,
        ProviderConfig(AnotherUserService, use_value=AnotherUserService()),
    ),
)(ModuleBaseExample2)
