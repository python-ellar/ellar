import pytest
from ellar.threading.sync_worker import (
    _SyncWorkerThread,
    execute_async_gen_with_sync_worker,
    execute_coroutine_with_sync_worker,
    sentinel,
)


async def coroutine_function():
    return "Coroutine Function"


async def coroutine_function_2():
    raise RuntimeError()


async def async_gen(after=None):
    for i in range(0, 10):
        if after and i > after:
            raise Exception("Exceeded")
        yield i


async def test_run_with_sync_worker_runs_async_function_synchronously(anyio_backend):
    res = execute_coroutine_with_sync_worker(coroutine_function())
    assert res == "Coroutine Function"


async def test_run_with_sync_worker_will_raise_an_exception(anyio_backend):
    with pytest.raises(RuntimeError):
        execute_coroutine_with_sync_worker(coroutine_function_2())


async def test_sync_worker_exists_wait_for_work_task(anyio_backend):
    worker = _SyncWorkerThread()
    worker.start()
    # exist waiting for a work task
    worker.work_queue.put(sentinel)
    worker.join()


async def test_sync_worker_execute_async_generator(anyio_backend):
    res = list(execute_async_gen_with_sync_worker(async_gen()))
    assert res == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


async def test_sync_worker_execute_async_generator_raises_exception(anyio_backend):
    worker = _SyncWorkerThread()
    worker.start()

    res = []
    with pytest.raises(Exception, match="Exceeded"):
        for item in worker.execute_generator(async_gen(6)):
            res.append(item)

    assert res == [0, 1, 2, 3, 4, 5, 6]


async def test_sync_worker_interrupt_function_works(anyio_backend):
    worker = _SyncWorkerThread()
    worker.start()

    res = []
    for item in worker.execute_generator(async_gen()):
        if len(res) == 7:
            worker.interrupt_generator()
            continue
        res.append(item)

    assert res == [0, 1, 2, 3, 4, 5, 6]
    worker.work_queue.put(sentinel)
    worker.join()
