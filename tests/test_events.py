from ellar.common.constants import NOT_SET
from ellar.core import Config
from ellar.events import EventHandler, EventManager


async def test_router_event_manager(anyio_backend):
    called = 0

    def valid_function_1():
        nonlocal called
        called += 1

    async def valid_function_2():
        nonlocal called
        called += 1

    route_manager = EventManager()
    # check event register
    route_manager += valid_function_1
    route_manager += valid_function_2

    assert len(route_manager) == 2
    route_manager_as_list = list(route_manager._handlers.values())
    function_handler_1, function_handler_2 = (
        route_manager_as_list[0],
        route_manager_as_list[1],
    )

    assert isinstance(function_handler_1, EventHandler)
    assert isinstance(function_handler_2, EventHandler)

    assert function_handler_1 == EventHandler(valid_function_1)
    assert function_handler_2 == EventHandler(valid_function_2)

    # assert function_handler_1.is_coroutine is False
    # assert function_handler_2.is_coroutine

    # check callable register
    lambda_function = route_manager.connect(lambda: valid_function_1())
    assert list(route_manager._handlers.values())[2] == lambda_function

    def another_function():
        valid_function_1()

    assert list(route_manager._handlers.values())[2] != another_function
    assert list(route_manager._handlers.values())[2] != NOT_SET

    await route_manager.run()
    assert called == 3

    # check event unregister
    route_manager -= valid_function_1
    route_manager.disconnect(valid_function_2)

    assert len(route_manager) == 1


async def test_valid_event_config(anyio_backend):
    called = 0

    def valid_function_1():
        nonlocal called
        called += 1

    config = Config(ON_REQUEST_STARTUP=[EventHandler(valid_function_1)])
    await config.ON_REQUEST_STARTUP[0].run()
    assert called == 1
