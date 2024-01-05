"""
Copied from BackendAI - http:github.com/lablup/backend.ai
https://github.com/lablup/backend.ai/blob/4a19001f9d1ae12be7244e14b304d783da9ea4f9/src/ai/backend/client/session.py#L128
"""
from __future__ import annotations

import asyncio
import enum
import inspect
import logging
import queue
import threading
import typing as t
from contextvars import Context, copy_context

_Item = t.TypeVar("_Item")

logger = logging.getLogger("ellar.sync_worker")


class _Sentinel(enum.Enum):
    """
    A special type to represent a special value to indicate closing/shutdown of queues.
    """

    TOKEN = 0

    def __bool__(self) -> bool:  # pragma: no cover
        # It should be evaluated as False when used as a boolean expr.
        return False


sentinel = _Sentinel.TOKEN


class _SyncWorkerThread(threading.Thread):
    work_queue: queue.Queue[
        t.Union[
            t.Tuple[t.Union[t.AsyncIterator, t.Coroutine], Context],
            _Sentinel,
        ]
    ]
    done_queue: queue.Queue[t.Union[t.Any, Exception]]
    stream_queue: queue.Queue[t.Union[t.Any, Exception, _Sentinel]]
    stream_block: threading.Event
    agen_shutdown: bool

    __slots__ = (
        "work_queue",
        "done_queue",
        "stream_queue",
        "stream_block",
        "agen_shutdown",
    )

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.work_queue = queue.Queue()
        self.done_queue = queue.Queue()
        self.stream_queue = queue.Queue()
        self.stream_block = threading.Event()
        self.agen_shutdown = False

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while True:
                item = self.work_queue.get()
                if item is sentinel:
                    break
                coro, ctx = item
                if inspect.isasyncgen(coro):
                    ctx.run(loop.run_until_complete, self.agen_wrapper(coro))  # type: ignore[arg-type]
                else:
                    try:
                        # FIXME: Once python/mypy#12756 is resolved, remove the type-ignore tag.
                        result = ctx.run(loop.run_until_complete, coro)  # type: ignore[arg-type]
                    except Exception as e:
                        self.done_queue.put_nowait(e)
                        self.work_queue.task_done()
                        raise e
                    else:
                        self.done_queue.put_nowait(result)
                        self.work_queue.task_done()

        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            pass
        except Exception as ex:
            logger.error(ex)
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.stop()
            loop.close()

    def execute(self, coro: t.Coroutine) -> t.Any:
        ctx = copy_context()  # preserve context for the worker thread
        try:
            self.work_queue.put((coro, ctx))
            result = self.done_queue.get()
            self.done_queue.task_done()
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            del ctx

    async def agen_wrapper(self, agen: t.Coroutine) -> None:
        self.agen_shutdown = False
        try:
            async for item in agen:  # type: ignore[attr-defined]
                self.stream_block.clear()
                self.stream_queue.put(item)
                # flow-control the generator.
                self.stream_block.wait()
                if self.agen_shutdown:
                    break
        except Exception as e:
            self.stream_queue.put(e)
        finally:
            self.stream_queue.put(sentinel)
            await agen.aclose()  # type: ignore[attr-defined]

    def execute_generator(self, async_gen: t.AsyncIterator[_Item]) -> t.Iterator[_Item]:
        ctx = copy_context()  # preserve context for the worker thread
        try:
            self.work_queue.put((async_gen, ctx))
            while True:
                item = self.stream_queue.get()
                try:
                    if item is sentinel:
                        break
                    if isinstance(item, Exception):
                        self.work_queue.put(sentinel)  # initial loop closing
                        raise item
                    yield item
                finally:
                    self.stream_block.set()
                    self.stream_queue.task_done()
        finally:
            del ctx

    def interrupt_generator(self) -> None:
        self.agen_shutdown = True
        self.stream_block.set()
        self.stream_queue.put(sentinel)


def execute_coroutine_with_sync_worker(coro: t.Coroutine) -> t.Any:
    _worker_thread = _SyncWorkerThread()
    _worker_thread.start()

    res = _worker_thread.execute(coro)

    _worker_thread.work_queue.put(sentinel)
    _worker_thread.join()

    return res


def execute_async_gen_with_sync_worker(
    async_gen: t.AsyncIterator[_Item],
) -> t.Iterator[_Item]:
    _worker_thread = _SyncWorkerThread()
    _worker_thread.start()

    for item in _worker_thread.execute_generator(async_gen):
        yield item

    _worker_thread.work_queue.put(sentinel)
    _worker_thread.join()
