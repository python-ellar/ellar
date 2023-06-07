# **Rate Limiting**
A common technique to protect applications from brute-force attacks is rate-limiting. 

To get started, you'll need to install the `ellar-throttler` package.

```shell
$(venv) pip install ellar-throttler
```

## **ThrottlerModule**

The `ThrottlerModule` is the main entry point for this package, and can be used in a synchronous or asynchronous manner. 
All the needs to be passed is the `ttl`, the time to live in seconds for the request tracker, and the `limit`, 
or how many times an endpoint can be hit before returning a 429 status code.

```python
from ellar.common import Module
from ellar_throttler import ThrottlerModule

@Module(modules=[
    ThrottlerModule.setup(ttl=60, limit=10)
])
class ApplicationModule:
    pass
```
The above would mean that 10 requests from the same IP can be made to a single endpoint in 1 minute.

```python
from ellar.common import Module
from ellar_throttler import ThrottlerModule, ThrottlerGuard
from ellar.core import Config, ModuleSetup, DynamicModule

def throttler_module_factory(module: ThrottlerModule, config: Config) -> DynamicModule:
    return module.setup(ttl=config['THROTTLE_TTL'], limit=config['THROTTLE_LIMIT'])


@Module(modules=[
    ModuleSetup(ThrottlerModule, inject=[Config], factory=throttler_module_factory)
])
class ApplicationModule:
    pass

# server.py
application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "dialerai.config:DevelopmentConfig"
    ),
    global_guards=[ThrottlerGuard]
)
```
The above is also a valid configuration for `ThrottleModule` registration if you want to work with config.

If you add the `ThrottlerGuard` to your application `global_guards`, then all the incoming requests will be throttled by default. 
This can also be omitted in favor of `@UseGuards(ThrottlerGuard)`. The global guard check can be skipped using the `@skip_throttle()` decorator mentioned later.

Example with `@UseGuards(ThrottlerGuard)`
```python
# project_name/controller.py
from ellar.common import Controller, UseGuards
from ellar_throttler import throttle, ThrottlerGuard

@Controller()
class AppController:

  @UseGuards(ThrottlerGuard)
  @throttle(limit=5, ttl=30)
  def normal(self):
      pass

```

### **ThrottlerModule Configuration Options:**

- `ttl`:	the number of seconds that each request will last in storage
- `limit`:	the maximum number of requests within the TTL limit
- `storage`: the storage setting for how to keep track of the requests. see [throttler storage](#throttlerstorageservice)


### Decorators

#### @throttle()
```
@throttle(*, limit: int = 20, ttl: int = 60)
```
This decorator will set `THROTTLER_LIMIT` and `THROTTLER_TTL` metadata on the route, for retrieval from the Reflector class. 
It can be applied to controllers and routes.

#### @skip_throttle()
```
@skip_throttle(skip: bool = True)
```
This decorator can be used to skip a route or a class or to negate the skipping of a route in 
a class that is skipped.

```python
# project_name/controller.py
from ellar.common import Controller, UseGuards
from ellar_throttler import ThrottlerGuard, skip_throttle

@skip_throttle()
@Controller()
@UseGuards(ThrottlerGuard)
class AppController:
  
    def do_skip(self):
        pass
  
    @skip_throttle(skip=False)
    def dont_skip(self):
        pass
```
In the above controller, `dont_skip` would be counted against and 
rate-limited while `do_skip` would not be limited in any way.

### **ThrottlerStorage**
Interface to define the methods to handle the details when it comes to keeping track of the requests.

Currently, the key is seen as an `MD5` hash of the IP the `class name` and the `function name`, 
to ensure that no unsafe characters are used.

The interface looks like this:

```python
import typing as t
from abc import ABC, abstractmethod

class IThrottlerStorage(ABC):
    @property
    @abstractmethod
    def storage(self) -> t.Dict[str, ThrottlerStorageOption]:
        """
        The internal storage with all the request records.
        The key is a hashed key based on the current context and IP.
        :return:
        """

    @abstractmethod
    async def increment(self, key: str, ttl: int) -> ThrottlerStorageRecord:
        """
        Increment the amount of requests for a given record. The record will
        automatically be removed from the storage once its TTL has been reached.
        :param key:
        :param ttl:
        :return:
        """
```
So long as the Storage service implements this interface, it should be usable by the `ThrottlerGuard`.

#### **ThrottlerStorageService**
`ThrottlerStorageService` extends `IThrottlerStorage` which defines the methods to handle the details when 
it comes to keeping track of the requests.

By default, `ThrottlerModule` uses `ThrottlerStorageService` when storage option is not provided.

#### **CacheThrottlerStorageService**
`CacheThrottlerStorageService` uses the **`default`** cache that is set up in the `CacheModule` to track throttling.
It depends on **`ICacheService`** which provided by **`CacheModule`**.

A quick example of how to set up `ThrottlerModule` with **CacheThrottlerStorageService**:

```python
from ellar.common import Module
from ellar_throttler import ThrottlerModule, CacheThrottlerStorageService
from ellar.cache import CacheModule
from ellar.cache.backends.local_cache import LocalMemCacheBackend

@Module(modules=[
    ThrottlerModule.setup(ttl=60, limit=10, storage=CacheThrottlerStorageService),
    CacheModule.setup(default=LocalMemCacheBackend(key_prefix='local'))
])
class ApplicationModule:
    pass
```

### **Proxies**
If you are working with multiple proxies, you can override the `get_tracker()` method to pull the value from the header or install 
[`ProxyHeadersMiddleware`](https://github.com/encode/uvicorn/blob/master/uvicorn/middleware/proxy_headers.py){target="_blank"}

```python
# throttler_behind_proxy.guard.py
from ellar_throttler import ThrottlerGuard
from ellar.di import injectable
from ellar.core.connection import HTTPConnection


@injectable()
class ThrottlerBehindProxyGuard(ThrottlerGuard):
    def get_tracker(self, connection: HTTPConnection) -> str:
        return connection.client.host  # individualize IP extraction to meet your own needs

# project_name/controller.py
from .throttler_behind_proxy import ThrottlerBehindProxyGuard

@Controller('')
@UseGuards(ThrottlerBehindProxyGuard)
class AppController:
    pass
```

### **Working with WebSockets**
To work with Websockets you can extend the `ThrottlerGuard` and override the `handle_request` method with the code below:
```python
from ellar_throttler import ThrottlerGuard
from ellar.di import injectable
from ellar.common import IExecutionContext
from ellar_throttler import ThrottledException

@injectable()
class WsThrottleGuard(ThrottlerGuard):
    async def handle_request(self, context: IExecutionContext, limit: int, ttl: int) -> bool:
        websocket_client = context.switch_to_websocket().get_client()

        host = websocket_client.client.host
        key = self.generate_key(context, host)
        result = await self.storage_service.increment(key, ttl)

        # Throw an error when the user reached their limit.
        if result.total_hits > limit:
            raise ThrottledException(wait=result.time_to_expire)
        
        return True
```
