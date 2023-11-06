import os

from ellar.auth.guards import GuardAPIKeyQuery
from ellar.common import (
    Controller,
    Inject,
    Module,
    ModuleRouter,
    exception_handler,
    get,
)
from ellar.core import ModuleBase, Request, WebSocket
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Host, Mount, Route, Router


def create_tmp_template_and_static_dir(tmpdir):
    template_folder = os.path.join(tmpdir, "templates")
    os.mkdir(template_folder)
    static_folder = os.path.join(tmpdir, "statics")
    os.mkdir(static_folder)

    path = os.path.join(static_folder, "example.txt")
    with open(path, "w") as file:
        file.write("<file content>")

    path = os.path.join(template_folder, "example.html")
    with open(path, "w") as file:
        file.write("<html>Hello World<html/>")
    return template_folder, static_folder


class AppAPIKey(GuardAPIKeyQuery):
    async def authentication_handler(self, connection, key):
        return key


def custom_sub_domain(request):
    return PlainTextResponse("Subdomain: " + request.path_params["subdomain"])


def all_users_page(request):
    return PlainTextResponse("Hello, everyone!")


def user_page(request):
    username = request.path_params["username"]
    return PlainTextResponse(f"Hello, {username}!")


sub_domain = Router(
    routes=[
        Route("/", custom_sub_domain),
    ]
)

users = Router(
    routes=[
        Route("/", endpoint=all_users_page),
        Route("/{username}", endpoint=user_page),
    ]
)

router = ModuleRouter()


@router.get("/func")
@router.head("/func")
def func_homepage(request: Inject[Request]):
    return PlainTextResponse("Hello, world!")


@router.get("/async")
async def async_homepage(request: Inject[Request]):
    return PlainTextResponse("Hello, world!")


@router.ws_route("/ws")
async def websocket_endpoint(session: Inject[WebSocket]):
    await session.accept()
    await session.send_text("Hello, world!")
    await session.close()


@Controller
class ClassBaseController:
    @get("/class")
    def class_function(self):
        return PlainTextResponse("Hello, world!")

    @get("/500")
    def runtime_error(self, request: Inject[Request]):
        raise RuntimeError()


@Module(
    routers=[
        Host("{subdomain}.example.org", app=sub_domain),
        Mount("/users", app=users),
        router,
    ],
    controllers=[ClassBaseController],
)
class ApplicationModule(ModuleBase):
    @exception_handler(405)
    async def method_not_allow_exception(self, ctx, exec):
        return JSONResponse({"detail": "Custom message"}, status_code=405)

    @exception_handler(500)
    async def error_500(self, ctx, exec):
        return JSONResponse({"detail": "Server Error"}, status_code=500)

    @exception_handler(HTTPException)
    async def http_exception(self, ctx, exc):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
