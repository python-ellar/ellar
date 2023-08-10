from time import sleep

from ellar.cache import Cache, CacheModule
from ellar.common import ModuleRouter, PlainTextResponse
from ellar.testing import Test


def test_cache_route_function_return_data():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @Cache(ttl=0.12)  # Cache for 3sec
    def homepage():
        nonlocal called_count

        called_count += 1
        return {"message": "Response Information cached."}

    client = Test.create_test_module(
        modules=[CacheModule.register_setup()],
        routers=[
            mr,
        ],
    ).get_test_client()

    for _i in range(2):
        client.get("/index")

    sleep(0.22)
    res = client.get("/index")

    assert res.json() == {"message": "Response Information cached."}
    assert res.status_code == 200
    assert called_count == 2


def test_cache_for_async_route_function_return_data():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @Cache(ttl=3)  # Cache for 3sec
    async def homepage():
        nonlocal called_count

        called_count += 1
        return {"message": "Response Information cached Async"}

    client = Test.create_test_module(
        modules=[CacheModule.register_setup()],
        routers=[
            mr,
        ],
    ).get_test_client()
    res = client.get("/index")
    for _i in range(2):
        res = client.get("/index")

    assert res.json() == {"message": "Response Information cached Async"}
    assert res.status_code == 200
    assert called_count == 1


def test_cache_for_async_route_function_return_response():
    called_count = 0

    mr = ModuleRouter()

    @mr.get("/index")
    @Cache(ttl=3)  # Cache for 3sec
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
    @Cache(ttl=2)  # Cache for 3sec
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
