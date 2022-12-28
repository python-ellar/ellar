Middlewares are functions that are called during requests before hitting a specific route handler.
Middleware functions can modify **request** and **response** objects during the `HTTP` or `WebSocket` connection. 

![middleware description image](../img/middleware.png)

Ellar Middlewares follows the [`Starlette ASGI Middleware`](https://www.starlette.io/middleware/) contract. The middlewares are set up in a pipeline fashion that creates a chain of request-response cycles.

During request, each `ASGI` Middleware must call another ASGI `app` passed to it during the middlewares instantiation and `await` its response. 

!!!info
    An `ASGI` type is any callable that takes `scope`, `receive` and `send` as arguments
    ```python
    
    def app(scope, receive, send):
        pass
    
    ```

```python
# ASGI Middleware Interface
import typing as t
from starlette.types import ASGIApp, Receive, Scope, Send


class EllarASGIMiddlewareStructure:
    def __init__(self, app: ASGIApp, **other_options: t.Any):
        self.app = app
        self.options = other_options
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        await self.app(scope, receive, send)
```

Actions that can be performed by middleware functions:

- Execute any code
- Make changes to request and response objects
- End the request-response cycle if need be
- Each middleware class or function must call `app` or `call_next` respectively else the request will be left without response

## **Dependency Injection**
This is still feature is still in progress

```python
import typing as t
from starlette.types import ASGIApp
from ellar.di import injectable


@injectable
class MyCustomService:
    pass


class EllarASGIMiddlewareStructure:
    def __init__(self, app: ASGIApp, service: MyCustomService, **other_options: t.Any):
        self.app = app
        self.options = other_options
        self.custom_service = service

```
## **Application Middleware**
Ellar applies some ASGI middleware necessary for resource protection, error handling, and context management.
They include:

- **`CORSMiddleware`**: - 'Cross-Origin-Resources-Sharing' - Adds appropriate `CORS` headers to outgoing responses in order to allow cross-origin requests from browsers.
- **`TrustedHostMiddleware`**: - Enforces that all incoming requests have a correctly set `Host` header, in order to guard against HTTP Host Header attacks.
- **`RequestServiceProviderMiddleware`**: - This inherits from `ServerErrorMiddleware`. It provides DI context during request and 
also ensures that application exceptions may return a custom 500 page, or display an application traceback in DEBUG mode.
- **`RequestVersioningMiddleware`**: This computes resource versioning info from request object based on configured resource versioning scheme at the application level.
- **`ExceptionMiddleware`**: - Adds exception handlers, so that particular types of expected exception cases can be associated with handler functions. For example raising `HTTPException(status_code=404)` within an endpoint will end up rendering a custom 404 page.

## Applying Middleware
Middleware can be applied through the application `config` - `MIDDLEWARES` variable. 

Let's apply some middleware in our previous project. At the project root level, open `config.py`.

Then apply the `GZipMiddleware` middleware as shown below.

```python
# project_name/config.py
import typing as t
from ellar.core.middleware import Middleware, GZipMiddleware
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    # Application middlewares
    MIDDLEWARE: t.Sequence[Middleware] = [
        Middleware(GZipMiddleware, minimum_size=1000)
    ]
    
```
!!! Hint
    This is how to apply any `ASGI` middlewares such as `GZipMiddleware`, `EllarASGIMiddlewareStructure`, and others available in the `Starlette` library.

## **Starlette Middlewares**
Let's explore other Starlette middlewares and other third party `ASGI` Middlewares

### **`GZipMiddleware`**
Handles GZip responses for any request that includes `"gzip"` in the Accept-Encoding header.
The middleware will handle both standard and streaming responses.

```python
# project_name/config.py
import typing as t
from ellar.core.middleware import Middleware, GZipMiddleware
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    # Application middlewares
    MIDDLEWARE: t.Sequence[Middleware] = [
        Middleware(GZipMiddleware, minimum_size=1000)
    ]
    
```

The following arguments are supported:

- **`minimum_size`** - Do not GZip responses that are smaller than this minimum size in bytes. Defaults to `500`.

The middleware won't GZip responses that already have a Content-Encoding set, to prevent them from being encoded twice.

### **`HTTPSRedirectMiddleware`**
Enforces that all incoming requests must either be `https` or `wss`.

Any incoming requests to `http` or `ws` will be redirected to the secure scheme instead.

```python
# project_name/config.py
import typing as t
from ellar.core.middleware import Middleware, HTTPSRedirectMiddleware
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    # Application middlewares
    MIDDLEWARE: t.Sequence[Middleware] = [
        Middleware(HTTPSRedirectMiddleware)
    ]
    
```

### **`TrustedHostMiddleware`**
This middleware is already part of ellar application middlewares. The middleware takes an argument `allowed_host` which can be configured in the configuration class.


```python
# project_name/config.py
import typing as t
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    # Application middlewares
    ALLOWED_HOSTS: t.List[str] = ['example.com', '*.example.com']
    
```
`ALLOWED_HOSTS` - A list of domain names that should be allowed as hostnames. 
Wildcard domains such as `*.example.com` are supported for matching subdomains. 
To allow any hostname either use `allowed_hosts=["*"]` or omit the middleware.

If an incoming request does not validate correctly then a `400` response will be sent.

### **`CORSMiddleware`**
Adds appropriate [`CORS headers`](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) to outgoing responses in order to allow cross-origin requests from browsers.

Since `CORSMiddleware` is part of default application middleware, let's see how to configure CORS arguments in ellar application.

```python
# project_name/config.py
import typing as t
...

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    # Application middlewares
    CORS_ALLOW_ORIGINS: t.List[str] = ["*"]
    CORS_ALLOW_METHODS: t.List[str] = ["*"]
    CORS_ALLOW_HEADERS: t.List[str] = ["*"]

    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_ORIGIN_REGEX: t.Optional[str] = None
    CORS_EXPOSE_HEADERS: t.Sequence[str] = ()
    CORS_MAX_AGE: int = 600
    
```

The following arguments are supported:

- `CORS_ALLOW_ORIGINS` - A list of origins that should be permitted to make cross-origin requests. eg. `['https://example.org', 'https://www.example.org']`. You can use `['*']` to allow any origin.
- `CORS_ALLOW_ORIGIN_REGEX` - A regex string to match against origins that should be permitted to make cross-origin requests. eg. `'https://.*\.example\.org'`.
- `CORS_ALLOW_METHODS` - A list of HTTP methods that should be allowed for cross-origin requests. Defaults to `['GET']`. You can use `['*']` to allow all standard methods.
- `CORS_ALLOW_HEADERS` - A list of HTTP request headers that should be supported for cross-origin requests. Defaults to `[]`. You can use `['*']` to allow all headers. The `Accept`, `Accept-Language`, `Content-Language` and `Content-Type` headers are always allowed for CORS requests.
- `CORS_ALLOW_CREDENTIALS` - Indicate that cookies should be supported for cross-origin requests. Defaults to `False`.
- `CORS_EXPOSE_HEADERS` - Indicate any response headers that should be made accessible to the browser. Defaults to `[]`.
- `CORS_MAX_AGE` - Sets a maximum time in seconds for browsers to cache CORS responses. Defaults to `600`.


#### CORS preflight requests

These are any `OPTIONS` request with `Origin` and `Access-Control-Request-Method` headers.

In this case the middleware will intercept the incoming request and respond with appropriate CORS headers, and either a `200` or `400` response for informational purposes.
The middleware responds to two particular types of HTTP request

#### Simple requests

Any request with an `Origin` header. In this case the middleware will pass the request through as normal, but will include appropriate CORS headers on the response.


### **`Other Middlewares`**

There are many other ASGI middlewares.
For example:

- [Sentry](https://docs.sentry.io/platforms/python/asgi/)
- [Uvicorn's ProxyHeadersMiddleware](https://github.com/encode/uvicorn/blob/master/uvicorn/middleware/proxy_headers.py)
- [MessagePack](https://github.com/florimondmanca/msgpack-asgi)

To see other available middlewares check [Starlette's Middleware docs](https://www.starlette.io/middleware/)  and the [ASGI Awesome List](https://github.com/florimondmanca/awesome-asgi).

!!! note "Technical Details"
    Most of the available middlewares come directly from Starlette. Ellar provides few required for its basic functionalities
