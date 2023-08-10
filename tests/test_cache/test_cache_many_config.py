from ellar.cache import Cache, CacheModule, ICacheService
from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.common import Controller, PlainTextResponse, get
from ellar.testing import Test


@Controller("")
class ExampleController:
    @get("/index-1")
    @Cache(ttl=1, backend="another")
    def index_1(self):
        return PlainTextResponse("ExampleController Cache 1")

    @get("/index-2")
    @Cache(ttl=1, backend="default")
    def index_2(self):
        return {"message": "ExampleController Cache 2"}


tm = Test.create_test_module(
    controllers=[ExampleController],
    modules=(CacheModule.register_setup(),),
    config_module={
        "CACHES": {
            "default": LocalMemCacheBackend(),
            "another": LocalMemCacheBackend(key_prefix="another", version=2),
        }
    },
)


def test_cache_backend_has_many_cache_backend():
    cache_service = tm.get(ICacheService)
    assert isinstance(cache_service.get_backend("another"), LocalMemCacheBackend)
    assert isinstance(cache_service.get_backend("default"), LocalMemCacheBackend)


def test_cache_operation_with_backend_works():
    cache_service = tm.get(ICacheService)
    client = tm.get_test_client(base_url="http://testserver")

    response = client.get("/index-1")
    assert response.text == "ExampleController Cache 1"
    result = cache_service.get("http://testserver/index-1:another", backend="another")
    assert result.body == b"ExampleController Cache 1"

    response = client.get("/index-2")
    assert response.json() == {"message": "ExampleController Cache 2"}
    result = cache_service.get("http://testserver/index-2:view", backend="default")
    assert result == {"message": "ExampleController Cache 2"}
