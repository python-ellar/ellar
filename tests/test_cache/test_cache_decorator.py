from time import sleep

from ellar.cache import CacheModule, cache
from ellar.common import ModuleRouter
from ellar.core.response import PlainTextResponse
from ellar.testing import Test


def test_cache_route_function_return_data():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @cache(ttl=0.12)  # cache for 3sec
    def homepage():
        nonlocal called_count

        called_count += 1
        return dict(message="Response Information cached.")

    client = Test.create_test_module(
        modules=[CacheModule.register_setup()],
        routers=[
            mr,
        ],
    ).get_test_client()

    for i in range(2):
        client.get("/index")

    sleep(0.22)
    res = client.get("/index")

    assert res.json() == dict(message="Response Information cached.")
    assert res.status_code == 200
    assert called_count == 2


def test_cache_for_async_route_function_return_data():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @cache(ttl=3)  # cache for 3sec
    async def homepage():
        nonlocal called_count

        called_count += 1
        return dict(message="Response Information cached Async")

    client = Test.create_test_module(
        modules=[CacheModule.register_setup()],
        routers=[
            mr,
        ],
    ).get_test_client()
    res = client.get("/index")
    for i in range(2):
        res = client.get("/index")

    assert res.json() == dict(message="Response Information cached Async")
    assert res.status_code == 200
    assert called_count == 1


def test_cache_for_async_route_function_return_response():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @cache(ttl=3)  # cache for 3sec
    async def homepage():
        nonlocal called_count

        called_count += 1
        return PlainTextResponse("Response Information cached Async")

    client = Test.create_test_module(
        modules=[CacheModule.register_setup()],
        routers=[
            mr,
        ],
    ).get_test_client()

    res = client.get("/index")

    assert res.text == "Response Information cached Async"
    assert res.status_code == 200
    assert called_count == 1


def test_cache_route_function_return_response():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @cache(ttl=2)  # cache for 3sec
    def homepage():
        nonlocal called_count

        called_count += 1
        return PlainTextResponse("Response Information cached")

    client = Test.create_test_module(
        modules=[CacheModule.register_setup()],
        routers=[
            mr,
        ],
    ).get_test_client()

    res = client.get("/index")

    assert res.text == "Response Information cached"
    assert res.status_code == 200
    assert called_count == 1
