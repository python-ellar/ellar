import pytest
from ellar.threading import run_as_sync


@run_as_sync
async def coroutine_function():
    return "Executed fine."


def test_coroutine_function_executes_fine():
    assert coroutine_function() == "Executed fine."


def test_run_async_fails_for_non_coroutine():
    with pytest.raises(AssertionError):

        @run_as_sync
        def sync_function():
            pass
