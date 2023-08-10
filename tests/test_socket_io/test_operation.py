import typing

import pytest
from ellar.socket_io import TestGateway
from ellar.socket_io.testing.module import RunWithServerContext

from .sample import EventGateway, GatewayOthers, GatewayWithGuards

# @pytest.fixture()
# from asgi_lifespan import LifespanManager
# from httpx import AsyncClient
# async def client() -> AsyncIterator[AsyncClient]:
#     async with LifespanManager(app):
#         async with AsyncClient(app=app, base_url="http://localhost") as client:
#             yield client


@pytest.mark.asyncio
class TestEventGateway:
    test_client = TestGateway.create_test_module(controllers=[EventGateway])

    async def test_socket_connection_work(self):
        my_response_message = []
        connected_called = False
        disconnected_called = False

        async with self.test_client.run_with_server() as ctx:

            @ctx.sio.event
            async def my_response(message):
                my_response_message.append(message)

            @ctx.sio.event
            async def disconnect():
                nonlocal disconnected_called
                disconnected_called = True

            @ctx.sio.event
            async def connect(*args):
                nonlocal connected_called
                await ctx.sio.emit("my_event", {"data": "I'm connected!"})
                connected_called = True

            await ctx.connect(socketio_path="/ws/")
            await ctx.wait()

        assert len(my_response_message) == 2
        assert my_response_message == [
            {"data": "Connected", "count": 0},
            {"data": "I'm connected!"},
        ]
        assert disconnected_called and connected_called

    async def test_broadcast_work(self):
        sio_1_response_message = []
        sio_2_response_message = []

        async with self.test_client.run_with_server() as ctx:
            ctx_2 = ctx.new_socket_client_context()

            @ctx.sio.on("my_response")
            async def my_response_case_1(message):
                sio_1_response_message.append(message)

            @ctx_2.sio.on("my_response")
            async def my_response_case_2(message):
                sio_2_response_message.append(message)

            await ctx.connect(socketio_path="/ws/")
            await ctx_2.connect(socketio_path="/ws/")

            await ctx.sio.emit(
                "my_broadcast_event", {"data": "Testing Broadcast"}
            )  # both sio_1 and sio_2 would receive this message

            await ctx.wait()
            await ctx_2.wait()

        assert len(sio_1_response_message) == 2
        assert sio_1_response_message == [
            {"data": "Connected", "count": 0},
            {"data": "Testing Broadcast"},
        ]

        assert len(sio_2_response_message) == 2
        assert sio_2_response_message == [
            {"data": "Connected", "count": 0},
            {"data": "Testing Broadcast"},
        ]


@pytest.mark.asyncio
class TestGatewayWithGuards:
    test_client = TestGateway.create_test_module(controllers=[GatewayWithGuards])

    async def test_socket_connection_work(self):
        my_response_message = []

        async with self.test_client.run_with_server() as ctx:

            @ctx.sio.event
            async def my_response(message):
                my_response_message.append(message)

            await ctx.connect(
                socketio_path="/ws-guard/", headers={"x-auth-key": "supersecret"}
            )
            await ctx.sio.emit("my_event", {"data": "Testing Broadcast"})
            await ctx.wait()

        assert my_response_message == [
            {"auth-key": "supersecret", "data": "Testing Broadcast"}
        ]

    async def test_event_with_header_work(self):
        my_response_message = []

        async with self.test_client.run_with_server() as ctx:

            @ctx.sio.event
            async def my_response(message):
                my_response_message.append(message)

            await ctx.connect(
                socketio_path="/ws-guard/", headers={"x-auth-key": "supersecret"}
            )
            await ctx.sio.emit("my_event_header", {"data": "Testing Broadcast"})
            await ctx.wait()

        assert my_response_message == [
            {"data": "Testing Broadcast", "x_auth_key": "supersecret"}
        ]

    async def test_event_with_plain_response(self):
        my_response_message = []

        async with self.test_client.run_with_server() as ctx:

            @ctx.sio.on("my_plain_response")
            async def message_receive(message):
                my_response_message.append(message)

            await ctx.connect(
                socketio_path="/ws-guard/", headers={"x-auth-key": "supersecret"}
            )
            await ctx.sio.emit("my_plain_response", {"data": "Testing Broadcast"})
            await ctx.wait()

        assert my_response_message == [
            {"data": "Testing Broadcast", "x_auth_key": "supersecret"}
        ]

    async def test_failed_to_connect(self):
        my_response_message = []

        async with self.test_client.run_with_server() as ctx:
            ctx = typing.cast(RunWithServerContext, ctx)

            @ctx.sio.on("error")
            async def error(message):
                my_response_message.append(message)

            await ctx.connect(
                socketio_path="/ws-guard/", headers={"x-auth-key": "supersecre"}
            )
            await ctx.sio.emit("my_event_header", {"data": "Testing Broadcast"})
            await ctx.wait()

        assert my_response_message == [{"code": 1011, "reason": "Authorization Failed"}]

    async def test_failed_process_message_sent(self):
        my_response_message = []

        async with self.test_client.run_with_server() as ctx:
            ctx = typing.cast(RunWithServerContext, ctx)

            @ctx.sio.on("error")
            async def error(message):
                my_response_message.append(message)

            await ctx.connect(
                socketio_path="/ws-guard/", headers={"x-auth-key": "supersecret"}
            )
            await ctx.sio.emit(
                "my_event_header", {"doesnt_exist_key": "Testing Broadcast"}
            )
            await ctx.wait()

        assert my_response_message == [
            {
                "code": 1007,
                "reason": [
                    {
                        "loc": ["body", "data"],
                        "msg": "none is not an allowed value",
                        "type": "type_error.none.not_allowed",
                    }
                ],
            }
        ]


@pytest.mark.asyncio
class TestGatewayExceptions:
    @pytest.mark.parametrize(
        "debug, result",
        [
            (
                True,
                [
                    {"code": 1011, "reason": "I dont have anything to run."},
                    {"code": 1009, "reason": "Message is too big"},
                ],
            ),
            (
                False,
                [
                    {"code": 1011, "reason": "Something went wrong"},
                    {"code": 1009, "reason": "Message is too big"},
                ],
            ),
        ],
    )
    async def test_exception_handling_works_debug_true_or_false(self, debug, result):
        test_client = TestGateway.create_test_module(
            controllers=[GatewayOthers], config_module={"DEBUG": debug}
        )
        my_response_message = []

        async with test_client.run_with_server() as ctx:
            ctx = typing.cast(RunWithServerContext, ctx)
            ctx2 = ctx.new_socket_client_context()

            @ctx.sio.on("error")
            async def error(message):
                my_response_message.append(message)

            @ctx2.sio.on("error")
            async def error_2(message):
                my_response_message.append(message)

            await ctx.connect(socketio_path="/ws-others/")
            await ctx2.connect(socketio_path="/ws-others/")

            await ctx.sio.emit("my_event", {})
            await ctx.wait()

            await ctx2.sio.emit("my_event_raise", {})
            await ctx2.wait()

        assert my_response_message == result

    async def test_message_with_extra_args(self):
        test_client = TestGateway.create_test_module(controllers=[GatewayOthers])
        my_response_message = []

        async with test_client.run_with_server() as ctx:
            ctx = typing.cast(RunWithServerContext, ctx)

            @ctx.sio.on("error")
            async def error(message):
                my_response_message.append(message)

            await ctx.connect(
                socketio_path="/ws-others/?query1=some-query1&query2=some-query2&?"
            )

            await ctx.sio.emit("extra_args", {})
            await ctx.wait()

        assert my_response_message == [
            {"code": 1009, "reason": {"query1": "some-query1", "query2": "some-query2"}}
        ]
