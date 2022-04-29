import pytest

from ellar.core.events import (
    ApplicationEventHandler,
    ApplicationEventManager,
    EventHandler,
    RouterEventManager,
)


def test_application_event_manager():
    called = 0

    def valid_function_1():
        nonlocal called
        called += 1

    async def valid_function_2():
        nonlocal called
        called += 1

    app_manager = ApplicationEventManager()
    app_manager += valid_function_1
    # check callable register
    lambda_function = app_manager(lambda: valid_function_1())

    assert len(app_manager) == 2

    function_handler_1, function_handler_2 = (
        app_manager._handlers[0],
        app_manager._handlers[1],
    )
    assert isinstance(function_handler_1, ApplicationEventHandler)
    assert isinstance(function_handler_2, ApplicationEventHandler)

    assert function_handler_1 == ApplicationEventHandler(valid_function_1)
    assert function_handler_2 == ApplicationEventHandler(lambda_function)

    app_manager.run()
    assert called == 2

    # check event unregister
    app_manager -= valid_function_1
    app_manager -= lambda_function

    assert len(app_manager) == 0

    app_manager(lambda some_args: f"{some_args}")
    app_manager.run(some_args="some_args")

    with pytest.raises(Exception, match="some_args"):
        app_manager.run()

    with pytest.raises(
        Exception, match="ApplicationEventHandler must be a non coroutine function"
    ):
        app_manager += valid_function_2

    with pytest.raises(
        Exception, match="ApplicationEventHandler must be a non coroutine function"
    ):
        ApplicationEventHandler(valid_function_2)


@pytest.mark.anyio
async def test_router_event_manager():
    called = 0

    def valid_function_1():
        nonlocal called
        called += 1

    async def valid_function_2():
        nonlocal called
        called += 1

    route_manager = RouterEventManager()
    # check event register
    route_manager += valid_function_1
    route_manager += valid_function_2

    assert len(route_manager) == 2

    function_handler_1, function_handler_2 = (
        route_manager._handlers[0],
        route_manager._handlers[1],
    )

    assert isinstance(function_handler_1, EventHandler)
    assert isinstance(function_handler_2, EventHandler)
    assert function_handler_1 == EventHandler(valid_function_1)
    assert function_handler_2 == EventHandler(valid_function_2)

    assert function_handler_1.is_coroutine is False
    assert function_handler_2.is_coroutine

    # check callable register
    lambda_function = route_manager(lambda: valid_function_1())
    assert route_manager._handlers[2] == EventHandler(lambda_function)

    await route_manager.async_run()
    assert called == 3

    # check event unregister
    route_manager -= valid_function_1
    route_manager -= valid_function_2

    assert len(route_manager) == 1
