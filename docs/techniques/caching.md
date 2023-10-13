# **Caching**
Caching refers to the process of storing frequently accessed data in a temporary storage area called a `cache`, 
in order to speed up access to that data in the future.

In computing, caching is used to optimize the performance of applications and systems by reducing the time it takes to retrieve data from slower or more distant storage. 
By caching data in a faster, more local storage location, the system can quickly retrieve the data without needing to go all the way to the original source of the data.

In Ellar, we provided several cache backends interface that interacts with different cache types to assist in cache endpoint responses or other relevant data.

## **Setting up the cache**
It's very simple to set up cache in Ellar but the crucial part is picking the cache type that is suitable for your application 
because some cache type behave differently and perform better and faster than others.

To set up cache, we need to use `CacheModule`. `CacheModule` provides two methods, `CacheModule.register_setup` and `CacheModule.setup`, for setting up `cache` in ellar applications.

=== "CacheModule Register Setup"
    This setup method requires you to defined `CACHES` variable containing 
    key value pairs of cache backends in `config.py` file.
    
    for example:
        
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.local_cache import LocalMemCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': LocalMemCacheBackend(ttl=300, key_prefix='local', version=1)
        }
    ```
    
    After that you register `CacheModule` to application modules
    ```python
    # project_name/root_module.py
    from ellar.cache import CacheModule
    from ellar.common import Module
    
    @Module(modules=[CacheModule.register_setup()])
    class ApplicationModule:
        pass
    ```
    The `register_setup` will read `CACHES` from application config and setup the `CacheService` appropriately.

=== "CacheModule Setup"
    The setup method requires direct definition of cache backend on the `CacheModule` setup function.
    
    for example:

    ```python
    # project_name/root_module.py
    from ellar.cache import CacheModule
    from ellar.cache.backends.local_cache import LocalMemCacheBackend
    from ellar.common import Module
    
    @Module(modules=[
        CacheModule.setup(
            default=LocalMemCacheBackend(ttl=300, key_prefix='default', version=1),
            local=LocalMemCacheBackend(key_prefix='local'),
            others=LocalMemCacheBackend(key_prefix='others'),
        )
    ])
    class ApplicationModule:
        pass
    ```
    In CacheModule.`setup`, the `default` parameter must be provided and other cache 
    backends will be defined as keyword-arguments just like `local` and `others` incase you want to set up more than one cache backend.

### **Memcached**
[Memcached](https://memcached.org/){target="_blank"} is an entirely memory-based cache server, originally developed to handle high loads at LiveJournal.com and subsequently open-sourced by Danga Interactive.

Memcached runs as a daemon and is allotted a specified amount of RAM. All it does is provide a fast interface for adding, retrieving and deleting data in the cache. All data is stored directly in memory.

After installing Memcached itself, you’ll need to install a Memcached binding. 
There are several Python Memcached bindings available; 

Ellar supports are [pylibmc](https://pypi.org/project/pylibmc/){target="_blank"} and [pymemcache](https://pypi.org/project/pymemcache/){target="_blank"}

For an example, lets assume you have a Memcached is running on localhost (127.0.0.1) port 11211, using the `pymemcache` or `pylibmc` binding:

=== "pymemcache"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': PyMemcacheCacheBackend(servers=['127.0.0.1:11211'])
        }
    ```
=== "pylibmc"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.pylib_cache import PyLibMCCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': PyLibMCCacheBackend(servers=['127.0.0.1:11211'])
        }
    ```
If Memcached is available through a local Unix socket file /tmp/memcached.sock using the `pymemcache` or `pylibmc` binding:


=== "pymemcache"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': PyMemcacheCacheBackend(servers=['/tmp/memcached.sock'])
        }
    ```
=== "pylibmc"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.pylib_cache import PyLibMCCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': PyLibMCCacheBackend(servers=['/tmp/memcached.sock'])
        }
    ```
if your Memcached is its ability to share a cache over multiple servers, then you can config that too
Lets assume the cache is shared over Memcached instances running on IP address 172.19.26.240 and 172.19.26.242, both on port 11211 or different ports


=== "pymemcache"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': PyMemcacheCacheBackend(servers=[
                '172.19.26.240:11211',
                '172.19.26.242:11212',
                '172.19.26.244:11213',
            ])
        }
    ```
=== "pylibmc"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.pylib_cache import PyLibMCCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': PyLibMCCacheBackend(servers=[
                '172.19.26.240:11211',
                '172.19.26.242:11212',
                '172.19.26.244:11213',
            ])
        }
    ```
For **pymemcache**, we provided some default configuration during initialization shown below:
```python
import pymemcache

_options = {
    'allow_unicode_keys': True,
    'default_noreply': False,
    'serde': pymemcache.serde.pickle_serde,
}
```

These can be changed by setting the desired value in `options` parameter during initialization. For example:

```python
# project_name/config.py

from ellar.core import ConfigDefaultTypesMixin
from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend

class DevelopmentConfig(ConfigDefaultTypesMixin):
    CACHES = {
        'default': PyMemcacheCacheBackend(servers=[
            '172.19.26.240:11211',
            '172.19.26.242:11212',
            '172.19.26.244:11213',
        ], options={'default_noreply': True})
    }
```

### **Redis**
[Redis](https://redis.io/){target="_blank"} is a high-performance, in-memory database that is commonly used for caching data. 
To get started with Redis, you will need to have a Redis server running on either your local machine or a remote server.

Once you have set up the Redis server, 
you will need to install the [Redis](https://pypi.org/project/redis/){target="_blank"} Python client library to be able 
to communicate with Redis from your Python code. 

To use redis in Ellar, you need to import RedisCacheBackend from `ellar.cache.backend.redis`.

Let's assume after setting up your redis server and it's running on localhost (127.0.0.1) port 6379:

=== "Redis"
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.redis import RedisCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': RedisCacheBackend(servers=['redis://127.0.0.1:6379'])
        }
    ```

=== "Redis - with username and password"
    Often Redis servers are protected with authentication. 
    In order to supply a username and password as follows:
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.redis import RedisCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': RedisCacheBackend(servers=['redis://username:password@127.0.0.1:6379'])
        }
    ```
=== "Redis - multiple server"
    If you have multiple Redis servers set up in the replication mode, you can specify the servers either as a semicolon or comma delimited string, or as a list. 
    While using multiple servers, write operations are performed on the first server (leader). 
    Read operations are performed on the other servers (replicas) chosen at random:
    
    ```python
    # project_name/config.py
    
    from ellar.core import ConfigDefaultTypesMixin
    from ellar.cache.backends.redis import RedisCacheBackend
    
    class DevelopmentConfig(ConfigDefaultTypesMixin):
        CACHES = {
            'default': RedisCacheBackend(servers=[
                'redis://127.0.0.1:6379', # leader
                'redis://127.0.0.1:6378', # read-replica 1
                'redis://127.0.0.1:6377', # read-replica 2
            ])
        }
    ```

### **Local-memory caching**
The local memory cache is the default caching mechanism used by Ellar, and it is automatically used if you do not specify a different caching backend in your config.py file. 
This cache stores cached data in memory, which provides fast access to cached data, and is ideal if you don't have the resources or capabilities to set up a separate caching server like Memcached. Its also thread-safe.

=== "Local Memory Cache"
```python
# project_name/config.py

from ellar.core import ConfigDefaultTypesMixin
from ellar.cache.backends.local_cache import LocalMemCacheBackend

class DevelopmentConfig(ConfigDefaultTypesMixin):
    CACHES = {
        'default': LocalMemCacheBackend()
    }
```

### **Custom Cache Backend**
You can create you own version of the cache backend. All you need is to inherit for `ellar.`

for example:
```python
# project_name/cache_backend.py
from ellar.cache.model import BaseCacheBackend

class CustomCacheBackend(BaseCacheBackend):
    pass

```
Then, in config.py
```python
# project_name/config.py

from ellar.core import ConfigDefaultTypesMixin
from .cache_backend import CustomCacheBackend

class DevelopmentConfig(ConfigDefaultTypesMixin):
    CACHES = {
        'default': CustomCacheBackend()
    }
```

## **Cache Arguments**

You can customize the behavior of each caching backend in Django by passing additional arguments when you configure the cache. The valid arguments that can be passed to each backend are as follows:

- **TIMEOUT**: The default timeout, in seconds, to use for the cache. This argument defaults to **300** seconds (5 minutes). You can set **TIMEOUT** to None so that, by default, cache keys never expire. A value of 0 causes keys to immediately expire
- **OPTIONS**: Any options that should be passed to the cache backend. The list of valid options will vary with each backend.
- **KEY_PREFIX**: A string that will be automatically prepended to all cache keys.
- **VERSION**: The default version number for cache keys.

```python
# project_name/config.py

from ellar.core import ConfigDefaultTypesMixin
from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend

class DevelopmentConfig(ConfigDefaultTypesMixin):
    CACHES = {
        'default': PyMemcacheCacheBackend(
            servers=['127.0.0.1:11211'], 
            options={'default_noreply': True}, 
            ttl=300, 
            version=1, 
            key_prefix='project_name'
        )
    }
```

## **Setting up More than One Cache Backend**
To set up multiple cache backends in Django, you can add additional entries to the `CACHES` variable in your `config.py` file. 
The `default` cache backend is typically defined first, followed by any additional cache backends you want to configure.

Here's an example `CACHES` setting that defines two cache backends:

```python
# project_name/config.py

from ellar.core import ConfigDefaultTypesMixin
from ellar.cache.backends.redis import RedisCacheBackend
from ellar.cache.backends.local_cache import LocalMemCacheBackend

class DevelopmentConfig(ConfigDefaultTypesMixin):
    CACHES = {
        'default': RedisCacheBackend(servers=['redis://127.0.0.1:6379'], key_prefix='project_name'),
        'secondary': LocalMemCacheBackend(ttl=300, key_prefix='project_name', version=1)
    }
```
 
## **CacheService (ICacheService)**
Ellar does not provide cache backends directly, but instead offers a caching service that manages all the configured cache backends in your application. 
The `CacheService` class serves as a wrapper for these cache backends and provides a uniform interface for interacting with them.

The `CacheService` class can be injected into your application's code as a dependency, allowing you to use it throughout your application without the need for direct instantiation. 
This approach promotes a more modular and extensible design, as well as better testability of your code.

The CacheService class provides methods like:

**class** _**CacheService(ICacheService)**_:

- **get**_**(key: str, version: str = None, backend: str = None)**_: gets `key` value from a specified cache backend.
- **get_async**_**(key: str, version: str = None, backend: str = None)**_: asynchronous version of `get` action
- **set**_**(key: str, value: t.Any, ttl: t.Union[float, int] = None, version: str = None,backend: str = None)**_: sets value to a key to a specified cache backend.
- **set_async**_**(key: str, value: t.Any, ttl: t.Union[float, int] = None, version: str = None,backend: str = None)**_: asynchronous version of `set` action
- **delete**_**(key: str, version: str = None, backend: str = None)**_: deletes a key from a specified cache backend.
- **delete_async**_**(key: str, version: str = None, backend: str = None)**_: asynchronous version of `delete` action
- **has_key**_**(key: str, version: str = None, backend: str = None)**_: checks if a key exist in a specified backend
- **has_key_async**_**(key: str, version: str = None, backend: str = None)**_: asynchronous version of `has_key` action
- **touch**_**(key: str, ttl: t.Union[float, int] = None, version: str = None, backend: str = None)**_: sets a new expiration for a key
- **touch_async**_**(key: str, ttl: t.Union[float, int] = None, version: str = None, backend: str = None)**_: asynchronous version of `touch` action
- **incr**_**(key: str, delta: int = 1, version: str = None, backend: str = None)**_: increments a value for a key by delta
- **incr_async**_**(key: str, delta: int = 1, version: str = None, backend: str = None)**_: asynchronous version of `incr` action
- **decr**_**(key: str, delta: int = 1, version: str = None, backend: str = None)**_: decrement a value for a key by delta
- **decr_async**_**(key: str, delta: int = 1, version: str = None, backend: str = None)**_: asynchronous version of `decr` action

!!! note
    If `backend=None`, `default` backend configuration is used.

These methods are available for each of the configured cache backends and can be used interchangeably with any backend.

## **Injecting CacheService**
`CacheService` is a core service registered in `EllarInjector` and can be injected as every other service.

For example, lets make `CacheService` available in our route function.

=== "Synchronous Route Function"
    ```python
    from ellar.common import get, Inject
    from ellar.cache import ICacheService
    
    ...
    @get('/cache-test')
    def my_route_function(self, cache_service: Inject[ICacheService]):
        cached_value = cache_service.get("my-key")
        if cached_value:
            return cached_value
        processed_value = 'some-value'
        cache_service.set('my-key', processed_value, timeout=300) # for 5mins
        return processed_value
    ```
=== "Asynchronous Route Function"
    ```python
    from ellar.common import get, Inject
    from ellar.cache import ICacheService
    
    ...
    @get('/cache-test')
    async def my_route_function(self, cache_service: Inject[ICacheService]):
        cached_value = await cache_service.get_async("my-key")
        if cached_value:
            return cached_value
        processed_value = 'some-value'
        await cache_service.set_async('my-key', processed_value, timeout=300) # for 5mins
        return processed_value
    ```


## **Using Cache Decorator**
Ellar provides a cache decorator that can be used to cache the responses of route functions. 
The cache decorator can be applied to a route function to automatically cache its response data for a specified amount of time.

The cache decorator takes the following arguments:

- `ttl`(time to live): the amount of time (in seconds) for which the response data should be cached.
- `key_prefix` (optional): a string that is used to prefix the cache key, allowing for easy differentiation between different cache items.
- `version` (optional): a string that is used to version the cache key, allowing for cache invalidation when the data schema changes.
- `backend` (optional): the name of the cache backend to use for storing the cached data. By default, the `default` cache backend is used.
- `make_key_callback` (optional): a callback function that can be used to generate a custom cache key. This function takes an `IExecutionContext` instance (which contains information about the request context) and key prefix, and should return the custom cache key to use.

!!! info
    `Cache` Decorator can also be applied to any controller class. 
    When this is done, all the routes response of that controller will be cached

We can rewrite the above example using `cache` decorator:
=== "Synchronous Route Function"
    ```python
    from ellar.common import get
    from ellar.cache import Cache
    ...
    @get('/cache-test')
    @Cache(ttl=300, version='v1', key_prefix='project_name')
    def my_route_function(self):
        processed_value = 'some-value'
        return processed_value
    ```
=== "Asynchronous Route Function"
    ```python
    from ellar.common import get
    from ellar.cache import Cache
    
    ...
    @get('/cache-test')
    @Cache(ttl=300, version='v1', key_prefix='project_name')
    async def my_route_function(self):
        processed_value = 'some-value'
        return processed_value
    ```

### **Adding Custom key gen function for cache Decorator**
By default, the `cache` decorator combines the route function's URL and the specified `key_prefix` value to generate the cache key used to store the response data. 
However, you can customize this behavior by providing a `make_key_callback` function to the cache decorator.

The `make_key_callback` function takes an `ExecutionContext` instance (which contains information about the request context) and the `key_prefix` value as input, and should return the custom cache key to use.

Here's an example of how to use a custom `make_key_callback` function with the cache decorator:
=== "Synchronous Route Function"
    ```python
    from ellar.common import get
    from ellar.cache import Cache
    from ellar.core import ExecutionContext
    from ellar.common.helper import get_name
    
    def make_key_function(ctx: ExecutionContext, key_prefix: str) -> str:
        function_name = get_name(ctx.get_handler())
        return "%s:%s:%s" % (function_name, key_prefix, ctx.switch_to_http_connection().get_client().url)
    
    ...
    @get("/my_endpoint")
    @Cache(ttl=60, make_key_callback=make_key_function)
    def my_endpoint(self):
        # Code to generate response data here
        processed_value = 'some-value'
        return processed_value
    ...
    ```
=== "Asynchronous Route Function"
    
    ```python
    from ellar.common import get
    from ellar.cache import Cache
    from ellar.core import ExecutionContext
    from ellar.common.helper import get_name
    
    def make_key_function(ctx: ExecutionContext, key_prefix: str) -> str:
        function_name = get_name(ctx.get_handler())
        return "%s:%s:%s" % (function_name, key_prefix, ctx.switch_to_http_connection().get_client().url)
    
    ...
    @get("/my_endpoint")
    @Cache(ttl=60, make_key_callback=make_key_function)
    async def my_endpoint(self):
        # Code to generate response data here
        processed_value = 'some-value'
        return processed_value
    ...
    ```
In this example, the `cache` decorator is applied to the `my_endpoint` route function, with a custom `make_key_callback` function specified. 

The `make_key_callback` function uses the `get_name` helper function to extract the name of the route function, and combines it with the `key_prefix` value and the request URL to generate the cache key.
