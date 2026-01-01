import typing as t
from contextlib import asynccontextmanager
from pathlib import Path

import socketio
from ellar.testing.module import Test, TestingModule
from ellar.testing.uvicorn_server import EllarUvicornServer
from starlette.routing import Host, Mount

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import ControllerBase, GuardCanActivate, ModuleRouter
    from ellar.core import ModuleBase
    from ellar.core.routing import EllarControllerMount
    from ellar.di import ProviderConfig


class RunWithServerContext:
    __slots__ = ("sio", "base_url", "sio_s")

    def __init__(self, sio: socketio.AsyncClient, base_url: str) -> None:
        self.sio = sio
        self.base_url: str = base_url
        self.sio_s = [sio]

    async def connect(
        self,
        path: str = "",
        namespaces: str = "/",
        socketio_path: str = "socket.io",
        **kwargs: t.Any,
    ) -> None:
        assert path == "" or path.startswith("/"), "Routed paths must start with '/'"
        await self.sio.connect(
            self.base_url + path,
            namespaces=namespaces,
            socketio_path=socketio_path,
            **kwargs,
        )

    async def wait(self, seconds: float = 0.5) -> None:
        await self.sio.sleep(seconds)

    def new_socket_client_context(self) -> "RunWithServerContext":
        sio = socketio.AsyncClient()
        self.sio_s.append(sio)
        return self.__class__(sio=sio, base_url=self.base_url)


class SocketIOTestingModule(TestingModule):
    @asynccontextmanager
    async def run_with_server(
        self, host: str = "127.0.0.1", port: int = 4000
    ) -> t.AsyncIterator[RunWithServerContext]:
        base_url = f"http://{host}:{port}"

        server = EllarUvicornServer(app=self.create_application(), host=host, port=port)

        await server.run_server()
        sio = socketio.AsyncClient()

        run_ctx = RunWithServerContext(sio=sio, base_url=base_url)

        yield run_ctx

        for item in run_ctx.sio_s:
            await item.shutdown()

        await server.tear_down()


class TestGateway(Test):
    TESTING_MODULE = SocketIOTestingModule

    @classmethod
    def create_test_module(
        cls,
        controllers: t.Sequence[t.Union[t.Type["ControllerBase"], t.Type]] = (),
        routers: t.Sequence[
            t.Union["ModuleRouter", "EllarControllerMount", Mount, Host, t.Callable]
        ] = (),
        providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = (),
        template_folder: t.Optional[str] = "templates",
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
        modules: t.Sequence[t.Union[t.Type, t.Any]] = (),
        application_module: t.Optional[t.Union[t.Type["ModuleBase"], str]] = None,
        global_guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        config_module: t.Optional[t.Union[str, t.Dict]] = None,
    ) -> SocketIOTestingModule:
        return t.cast(
            SocketIOTestingModule,
            super().create_test_module(
                controllers=controllers,
                routers=routers,
                providers=providers,
                template_folder=template_folder,
                base_directory=base_directory,
                static_folder=static_folder,
                modules=modules,
                application_module=application_module,
                global_guards=global_guards,
                config_module=config_module,
            ),
        )
