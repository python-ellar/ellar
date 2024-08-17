import asyncio
import typing as t

import uvicorn
from starlette.types import ASGIApp


class EllarUvicornServer(uvicorn.Server):
    """
    Uvicorn Server for testing purpose.


    @pytest_asyncio.fixture
    async def start_server():
        server = EllarUvicornServer(asgi_app)
        await server.start_up()
        yield
        await server.tear_down()

    """

    def __init__(self, app: ASGIApp, host: str = "127.0.0.1", port: int = 8000):
        self._startup_done = asyncio.Event()
        self._serve_task: t.Optional[t.Awaitable[t.Any]] = None
        super().__init__(config=uvicorn.Config(app, host=host, port=port))

    async def startup(self, sockets: t.Optional[t.List[t.Any]] = None) -> None:
        """Override uvicorn startup"""
        await super().startup(sockets)
        self.config.setup_event_loop()
        self._startup_done.set()

    async def run_server(self) -> None:
        """Start up server asynchronously"""
        self._serve_task = asyncio.create_task(self.serve())
        await self._startup_done.wait()

    async def tear_down(self) -> None:
        """Shut down server asynchronously"""
        self.should_exit = True
        if self._serve_task:
            await self._serve_task
