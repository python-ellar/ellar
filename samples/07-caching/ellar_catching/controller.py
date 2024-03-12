import ellar.common as ecm
from ellar.cache import Cache, ICacheService
from ellar.utils import get_name


def _make_key_function(ctx: ecm.IExecutionContext, key_prefix: str) -> str:
    function_name = get_name(ctx.get_handler())
    return "%s:%s:%s" % (
        function_name,
        key_prefix,
        ctx.switch_to_http_connection().get_client().url,
    )


@ecm.Controller()
class CacheControllerTest(ecm.ControllerBase):
    @ecm.get("/using-icache-service", response=str)
    def using_icache(self, cache_service: ecm.Inject[ICacheService]):
        cached_value = cache_service.get("my-key", backend="secondary")
        if cached_value:
            return cached_value

        print(f"[{self.__class__.__name__}][using_icache] => creates new value")

        processed_value = "This result will be cached for 60 secs thereafter `using_icache` function will be called again."
        cache_service.set(
            "my-key", processed_value, ttl=60, backend="secondary"
        )  # for 1 minute
        return processed_value

    @ecm.get("/using-decorator", response=str)
    @Cache(ttl=60, backend="default")
    async def using_decorator(self):
        print(f"[{self.__class__.__name__}][using_decorator] => creates new value")

        return "This result will be cached for 60 secs thereafter `using_decorator` function will be called again."

    @ecm.get("/using-decorator-with-key-difference", response=str)
    @Cache(ttl=60, make_key_callback=_make_key_function)
    def using_modify_key(self):
        print(f"[{self.__class__.__name__}][using_modify_key] => creates new value")

        return "This result will be cached for 60 secs thereafter `using_modify_key` function will be called again."
