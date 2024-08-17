# **Rate Limiting**

`Ellar-Throttler` package offers a robust rate-limiting module designed specifically for Ellar, 
providing efficient throttling capabilities for web applications.

## **Installation**
To install the Ellar Throttler package, use pip within your virtual environment:

```shell
$(venv) pip install ellar-throttler
```

## **Usage**

### **ThrottlerModule**
The **`ThrottlerModule`** serves as the primary interface for configuring throttling mechanisms across the entire Ellar application.

#### ThrottlerModule Parameters

| Parameter          | Description                                                                                          |
|--------------------|------------------------------------------------------------------------------------------------------|
| throttlers         | A list of `IThrottleModel` instances defining various throttling mechanisms.                         |
| storage            | An `IThrottlerStorage` service, instance, or class responsible for tracking throttling.              |
| error_message      | A customizable string to replace the default throttler error message.                                |
| ignore_user_agents | An array of user-agent strings to exempt from throttling.                                            |
| skip_if            | A global function that evaluates `ExecutionContext` and returns a boolean to bypass throttler logic. |

#### ThrottlerModule Setup
Similar to other Ellar modules, you can set up `ThrottlerModule` directly using the `setup` function or configure it via `register_setup`.

```python title="root_module.py"
from ellar.common import Module
from ellar_throttler import ThrottlerModule, AnonymousThrottler, UserThrottler

@Module(modules=[
    ThrottlerModule.setup(
        throttlers=[
            AnonymousThrottler(limit=100, ttl=(60*5), name='anon'), # Allow 100 requests per 5 minutes for anonymous users
            UserThrottler(limit=2000, ttl=(60*60*24), name='user'), # Allow 2000 requests per day for authenticated users
        ]
    )
])
class ApplicationModule:
    pass
```

In the above setup, we've specified a limit of 100 requests per 5 minutes for anonymous users and 2000 requests per day for authenticated users.

Alternatively, configuration-based setup is demonstrated below:

```python title="config.py"
...
from ellar_throttler import AnonymousThrottler, UserThrottler

class BaseConfig:
    ELLAR_THROTTLER_CONFIG: {
        'throttlers': [
            AnonymousThrottler(limit=100, ttl=(60*5), name='anon'), # Allow 100 requests per 5 minutes for anonymous users
            UserThrottler(limit=2000, ttl=(60*60*24), name='user'), # Allow 2000 requests per day for authenticated users
        ]
    }
```

Then, in `ApplicationModule`:

```python
from ellar.common import Module
from ellar_throttler import ThrottlerModule

@Module(modules=[
    ThrottlerModule.register_setup()
])
class ApplicationModule:
    pass
```

### **Throttle All Routes**
To apply throttling to all incoming requests, utilize `ThrottlerInterceptor` globally, as illustrated below:

```python
from ellar.app import AppFactory
from ellar_throttler import ThrottlerInterceptor
from .module import AppModule

app = AppFactory.create_from_app_module(AppModule)
app.use_global_interceptors(ThrottlerInterceptor)
```

### **Decorators**

This package introduces two decorators, `Throttle` and `SkipThrottle`, 
designed to provide additional metadata for the `ThrottlerInterceptor`, guiding its throttling behavior or 
bypassing it for decorated controllers or route functions.

#### **Using `Throttle` Decorator**

The `Throttle` decorator applies the `ThrottlerInterceptor` and allows for overriding 
configurations for any throttler model defined in the `ThrottlerModule.throttlers` list.

```python title="controllers.py"
from ellar_throttler import Throttle
from ellar.common import Controller, get


@Controller("/limit")
@Throttle(intercept=True)
class LimitController:
    def __init__(self, app_service: AppService):
        self.app_service = app_service

    @get()
    def get_throttled(self, use_auth: bool):
        return self.app_service.success(use_auth)
```

In the above example, by setting `intercept=True` within **@Throttle**, 
the `ThrottlerInterceptor` is applied to all routes within the `LimitController`. 
This feature is particularly useful when `ThrottlerInterceptor` is not globally applied.

Additionally, the **@Throttle** decorator can be used on a route level:

```python
@get()
@Throttle(intercept=True)
def get_throttled(self, use_auth: bool):
    return self.app_service.success(use_auth)
```

Another application of the **@Throttle** decorator is to override `ttl` and `limit` for a specific configured throttler model:

```python
@Controller("/limit")
@Throttle(intercept=True, anon={'ttl': 100, 'limit': 30})
class LimitController:
    def __init__(self, app_service: AppService):
        self.app_service = app_service

    @get()
    def get_throttled(self, use_auth: bool):
        return self.app_service.success(use_auth)
```

In this scenario, different `ttl` and `limit` values are applied to the **LimitController** 
when executing against a throttler model named `anon`.

#### **Using `SkipThrottle` Decorator**

The `SkipThrottle` decorator marks a decorated class or route function with metadata 
used by `ThrottlerInterceptor` to entirely bypass throttling or selectively skip specific throttler models.

For instance, if using `ThrottlerInterceptor` as a global interceptor and wishing to bypass throttling for `LimitController`:

```python
from ellar_throttler import SkipThrottle
from ellar.common import Controller, get


@Controller("/limit")
@SkipThrottle()
class LimitController:
    def __init__(self, app_service: AppService):
        self.app_service = app_service

    @get()
    def get_throttled(self, use_auth: bool):
        return self.app_service.success(use_auth)
```

This setup will bypass all throttling models for `LimitController`. If only the `user` throttler model needs to be skipped:

```python
from ellar_throttler import SkipThrottle
from ellar.common import Controller, get


@Controller("/limit")
@SkipThrottle(user=True)
class LimitController:
    def __init__(self, app_service: AppService):
        self.app_service = app_service

    @get()
    def get_throttled(self, use_auth: bool):
        return self.app_service.success(use_auth)
```

This configuration skips all throttling models except for the one named `user`.

## **IThrottlerModel**

The **IThrottlerModel** serves as an interface for defining attributes and properties specific to a throttler. 
The package provides several `ThrottlerModel` implementations to facilitate usage.

### **AnonymousThrottler**

The `AnonymousThrottler` model is designed for throttling unauthenticated users, utilizing their 
`client.host` address as a key for throttling purposes. It exempts authenticated requests and is 
ideal for limiting requests from unknown sources.

```python
from ellar_throttler import AnonymousThrottler

class BaseConfig:
    ELLAR_THROTTLER_CONFIG: {
        'throttlers': [
            # Configuring burst and sustained throttling for unauthenticated users
            AnonymousThrottler(limit=100, ttl=(60*5), name='burst'),
            AnonymousThrottler(limit=1000, ttl=(60*60*24), name='sustain'),
        ]
    }
```

### **UserThrottler**

The `UserThrottler` model is tailored for throttling authenticated users, 
utilizing user `id` or `sub` to generate a key for throttling. Unauthenticated requests 
resort to using the `client.host` address for generating a unique key. 

```python
from ellar_throttler import UserThrottler

class BaseConfig:
    ELLAR_THROTTLER_CONFIG: {
        'throttlers': [
            # Configuring burst and sustained throttling for authenticated users
            UserThrottler(limit=100, ttl=(60*5), name='burst'),
            UserThrottler(limit=1000, ttl=(60*60*24), name='sustain'),
        ]
    }
```

## **IThrottlerStorage**

The `IThrottlerStorage` interface defines methods for managing the details of request tracking within the throttler. 
This package provides two implementations of `IThrottlerStorage`:

#### `ThrottlerStorageService`: 
This service offers in-memory storage for throttling, suitable for testing request throttling in development environments. 
When configuring `ThrottlerModule`, if no storage parameter is provided, `ThrottlerStorageService` is selected by default.

```python title="root_module.py"
from ellar.common import Module
from ellar_throttler import ThrottlerModule, AnonymousThrottler, UserThrottler, ThrottlerStorageService

@Module(modules=[
    ThrottlerModule.setup(
        throttlers=[
            AnonymousThrottler(limit=200, ttl=(60*24), name='anon'), # 200/day for anonymous requests
            UserThrottler(limit=1000, ttl=(60*24), name='user'), # 1000/day for authenticated requests
        ],
        # storage=ThrottlerStorageService() use as an instance OR
        storage=ThrottlerStorageService
    )
])
class ApplicationModule:
    pass
```

#### `CacheThrottlerStorageService`
This service utilizes the default caching setup in your Ellar application, providing more dynamic storage options. 
It requires setting up caching, where various storage backends are available through 
[`CacheModule`](https://python-ellar.github.io/ellar/techniques/caching/). 
In the example below, caching is set up using the Redis backend.

```python title="root_module.py"
from ellar.common import Module
from ellar.cache import CacheModule
from ellar.cache.backends.redis import RedisCacheBackend
from ellar_throttler import ThrottlerModule, AnonymousThrottler, UserThrottler, CacheThrottlerStorageService

@Module(modules=[
    ThrottlerModule.setup(
        throttlers=[
            AnonymousThrottler(limit=100, ttl=(60*5), name='anon'), # 200/5mins for anonymous requests
            UserThrottler(limit=2000, ttl=(60*60*24), name='user'), # 2000/24hrs for authenticated requests
        ],
        storage=CacheThrottlerStorageService
    ),
    CacheModule.setup(default=RedisCacheBackend(servers=['redis://127.0.0.1:6379']))
])
class ApplicationModule:
    pass
```

To modify the caching type used in `CacheThrottlerStorageService`, 
you need to extend the class and set the `cache_backend` to point to the desired caching service backend:

```python
from ellar.di import injectable
from ellar.cache import ICacheService
from ellar_throttler import CacheThrottlerStorageService


@injectable()
class MyNewCacheThrottlerStorageService(CacheThrottlerStorageService):
    def __init__(self, cache_service: ICacheService) -> None:
        super().__init__(cache_service)
        self.cache_backend = 'my_backend'

    
# in root_module.py
@Module(modules=[
    ThrottlerModule.setup(
        throttlers=[
            AnonymousThrottler(limit=100, ttl=(60*5), name='anon'), # 200/5mins for anonymous requests
            UserThrottler(limit=2000, ttl=(60*60*24), name='user'), # 2000/24hrs for authenticated requests
        ],
        storage=MyNewCacheThrottlerStorageService
    ),
    CacheModule.setup(
        default=RedisCacheBackend(servers=['redis://127.0.0.1:6379']),
        my_backend=RedisCacheBackend(servers=['redis://127.0.0.1:6379'])
    )
])
class ApplicationModule:
    pass
```

## **Proxies**

If you're working with multiple proxies, 
you may need to install [`ProxyHeadersMiddleware`](https://github.com/encode/uvicorn/blob/master/uvicorn/middleware/proxy_headers.py).

## **Working with WebSockets**

To utilize WebSockets, you can include `WebsocketThrottler` in the list of throttlers for your application.

```python
from ellar.common import Module
from ellar.cache import CacheModule
from ellar.cache.backends.redis import RedisCacheBackend
from ellar_throttler import ThrottlerModule, AnonymousThrottler, UserThrottler, CacheThrottlerStorageService, model

@Module(modules=[
    ThrottlerModule.setup(
        throttlers=[
            # HTTP Throttling Models
            AnonymousThrottler(limit=200, ttl=(60*24)), # 200/day for anonymous requests 
            UserThrottler(limit=1000, ttl=(60*24)), # 1000/day for authenticated requests
            # Websocket Throttling Models
            model.WebsocketThrottler('ws-burst', limit=200, ttl=(60*24)), # 200/day  
            model.WebsocketThrottler('ws-sustain', limit=2000, ttl=(60*24)), # 2000/day 
        ],
        storage=CacheThrottlerStorageService
    ),
    CacheModule.setup(default=RedisCacheBackend(servers=['redis://127.0.0.1:6379']))
])
class ApplicationModule:
    pass
```

The `WebsocketThrottler` only runs within the websocket environment. 
Additionally,
note
that `WebsocketThrottler` workers like `UserThrottler` for an authenticated 
request and `AnonymousThrottler` for anonymous request.
