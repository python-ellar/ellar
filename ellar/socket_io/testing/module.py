import typing as t
from contextlib import asynccontextmanager

import socketio
from ellar.testing.module import Test, TestingModule
from ellar.testing.uvicorn_server import EllarUvicornServer


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
