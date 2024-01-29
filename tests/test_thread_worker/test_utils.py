import pytest
from ellar.threading import run_as_async


@run_as_async
async def coroutine_function():
    return "Executed fine."


def test_coroutine_function_executes_fine():
    assert coroutine_function() == "Executed fine."


def test_run_async_fails_for_non_coroutine():
    with pytest.raises(AssertionError):

        @run_as_async
        def sync_function():
            pass
