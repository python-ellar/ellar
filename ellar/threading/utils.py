import asyncio
import functools
import typing as t

from ellar.threading.sync_worker import execute_coroutine


def run_as_sync(f: t.Callable) -> t.Callable:
    """
    Runs Coroutines Synchronously

    eg:
    ```python
        @click.command()
        @click.argument('name')
        @click.run_as_async
        async def print_name(name: str):
            click.echo(f'Hello {name}, this is an async command.')
    ```
    """
    assert asyncio.iscoroutinefunction(f), "Decorated function must be Coroutine"

    @functools.wraps(f)
    def _decorator(*args: t.Any, **kw: t.Any) -> t.Any:
        return execute_coroutine(f(*args, **kw))

    return _decorator
