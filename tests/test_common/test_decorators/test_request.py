from ellar.common import on_shutdown, on_startup
from ellar.constants import ON_REQUEST_SHUTDOWN_KEY, ON_REQUEST_STARTUP_KEY
from ellar.core.events import EventHandler


@on_startup
def on_startup_func():
    pass  # pragma: no cover


@on_startup()
async def on_startup_func_2():
    pass  # pragma: no cover


@on_shutdown
def on_shutdown_func():
    pass  # pragma: no cover


@on_shutdown()
async def on_shutdown_func_2():
    pass  # pragma: no cover


def test_on_startup_decorator_is_converted_to_event_handler():
    assert hasattr(on_startup_func, ON_REQUEST_STARTUP_KEY)
    attr = getattr(on_startup_func, ON_REQUEST_STARTUP_KEY)
    assert isinstance(attr, EventHandler)
    assert attr.is_coroutine is False
    assert attr.handler is on_startup_func

    attr2 = getattr(on_startup_func_2, ON_REQUEST_STARTUP_KEY)
    assert isinstance(attr2, EventHandler)
    assert attr2.is_coroutine
    assert attr2.handler is on_startup_func_2


def test_on_shutdown_decorator_is_converted_to_event_handler():
    assert hasattr(on_shutdown_func, ON_REQUEST_SHUTDOWN_KEY)
    attr = getattr(on_shutdown_func, ON_REQUEST_SHUTDOWN_KEY)
    assert isinstance(attr, EventHandler)
    assert attr.is_coroutine is False
    assert attr.handler is on_shutdown_func

    attr2 = getattr(on_shutdown_func_2, ON_REQUEST_SHUTDOWN_KEY)
    assert isinstance(attr2, EventHandler)
    assert attr2.is_coroutine
    assert attr2.handler is on_shutdown_func_2
