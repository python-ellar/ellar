from ellar.cache import ICacheService
from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.common import Controller, cache, get
from ellar.core import TestClientFactory
from ellar.core.response import PlainTextResponse
from ellar.helper.importer import get_class_import


class ManyCacheBackendConfig:
    CACHES = {
        "default": LocalMemCacheBackend(key_prefix="default"),
        "another": LocalMemCacheBackend(key_prefix="another", version=2),
    }


@Controller("")
class ExampleController:
    @get("/index-1")
    @cache(timeout=1, backend="another")
    def index_1(self):
        return PlainTextResponse("ExampleController cache 1")

    @get("/index-2")
    @cache(timeout=1, backend="default")
    def index_2(self):
        return dict(message="ExampleController cache 2")


tm = TestClientFactory.create_test_module(
    controllers=[ExampleController],
    config_module=get_class_import(ManyCacheBackendConfig),
)


def test_cache_backend_has_many_cache_backend():
    cache_service = tm.app.injector.get(ICacheService)
    assert isinstance(cache_service._get_backend("another"), LocalMemCacheBackend)
    assert isinstance(cache_service._get_backend("default"), LocalMemCacheBackend)


def test_cache_operation_with_backend_works():
    cache_service = tm.app.injector.get(ICacheService)
    client = tm.get_client(base_url="http://testserver")

    response = client.get("/index-1")
    assert response.text == "ExampleController cache 1"
    result = cache_service.get("http://testserver/index-1:view", backend="another")
    assert result.body == b"ExampleController cache 1"

    response = client.get("/index-2")
    assert response.json() == dict(message="ExampleController cache 2")
    result = cache_service.get("http://testserver/index-2:view", backend="default")
    assert result == dict(message="ExampleController cache 2")
